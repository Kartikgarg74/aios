#!/usr/bin/env python3
"""
Central Orchestrator (Port 9000)
Coordinates between all MCP servers and handles command routing
"""

import os
import json
import logging
import asyncio
import aiohttp
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis
import uuid
from contextlib import asynccontextmanager
from security.auth import get_current_active_user, create_access_token, verify_password, get_password_hash
from security.api_key_manager import APIKeyManager
from fastapi.security import OAuth2PasswordRequestForm, APIKeyHeader
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from gpt_oss_mcp_server.main_mcp_server import AppContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configurations
SERVER_PORTS = {
    "python": 8000,
    "browser": 8001,
    "system": 8002,
    "communication": 8003,
    "ide": 8004,
    "github": 8005,
    "voice_ui": 8006
}

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    servers: Dict[str, str]
    active_sessions: int
    message_queue_status: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[Dict[str, Any]] = None
    disk_usage: Optional[Dict[str, Any]] = None

class CommandRequest(BaseModel):
    command: str
    parameters: Dict[str, Any]
    target_server: Optional[str] = None
    session_id: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical

class CommandResponse(BaseModel):
    command_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime
    execution_time: float

class SessionInfo(BaseModel):
    session_id: str
    user_id: Optional[str] = None  # New field for user association
    created_at: datetime
    last_activity: datetime
    active_servers: List[str]
    pending_commands: List[str]
    session_data: Dict[str, Any] = Field(default_factory=dict) # New field for arbitrary session data

class ServerHealth(BaseModel):
    name: str
    status: str
    last_check: datetime
    response_time: float
    error: Optional[str] = None

app = FastAPI(title="Central Orchestrator", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global variables
redis_client = None
active_sessions: Dict[str, SessionInfo] = {}
server_health_cache: Dict[str, ServerHealth] = {}
command_history: List[CommandResponse] = []
websocket_connections: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global redis_client
    redis_client = redis.from_url("redis://localhost", encoding="utf8", decode_responses=True)
    await FastAPILimiter.init(redis_client)
    logger.info("FastAPI Limiter initialized.")
    asyncio.create_task(monitor_server_health())
    app.state.app_context = AppContext() # Initialize AppContext and attach to app state
    yield
    # Shutdown logic
    if redis_client:
        await redis_client.close()
    logger.info("Central Orchestrator shutdown complete.")

app = FastAPI(title="Central Orchestrator", version="1.0.0", lifespan=lifespan)

async def initialize_orchestrator():
    """Initialize the orchestrator"""
    global redis_client
    try:
        # Initialize Redis connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis unavailable, using in-memory storage: {e}")
        redis_client = None
    
    # Start health monitoring
    asyncio.create_task(monitor_server_health())

async def cleanup_orchestrator():
    """Cleanup resources"""
    if redis_client:
        redis_client.close()
    logger.info("Orchestrator shutdown complete")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for orchestrator"""
    servers_status = {}
    for server_name in SERVER_PORTS:
        health = server_health_cache.get(server_name)
        servers_status[server_name] = health.status if health else "unknown"
    
    queue_status = "connected" if redis_client else "memory_only"
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        servers=servers_status,
        active_sessions=len(active_sessions),
        message_queue_status=queue_status,
        cpu_usage=cpu_percent,
        memory_usage={
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        },
        disk_usage={
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
    )

api_key_manager = APIKeyManager(api_keys_file="./security/api_keys.json")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key and api_key_manager.validate_api_key(api_key):
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate API Key")

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real application, you would fetch user from a database
    # For demonstration, let's use a hardcoded user
    user_db = {"username": "testuser", "hashed_password": get_password_hash("testpassword")}

    if form_data.username != user_db["username"] or not verify_password(form_data.password, user_db["hashed_password"]):
        raise HTTPException(
            status_code=400, detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user_db["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/command", response_model=CommandResponse, dependencies=[Depends(RateLimiter(times=5, seconds=1))])
async def execute_command(request: CommandRequest, current_user: str = Depends(get_current_active_user), api_key: Optional[str] = Depends(get_api_key)):
    """Execute a command through the orchestrator"""
    command_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        # Determine target server
        target_server = request.target_server or await determine_target_server(request.command)
        
        if not target_server:
            raise HTTPException(status_code=400, detail="Could not determine target server")
        
        # Validate server health
        health = server_health_cache.get(target_server)
        if not health or health.status != "healthy":
            raise HTTPException(status_code=503, detail=f"Target server {target_server} is unavailable")
        
        # Execute command
        result = await send_command_to_server(target_server, request.command, request.parameters)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response = CommandResponse(
            command_id=command_id,
            status="success",
            result=result,
            timestamp=datetime.now(),
            execution_time=execution_time
        )
        
        # Store in history
        command_history.append(response)
        if len(command_history) > 1000:
            command_history.pop(0)
        
        # Update session
        if request.session_id:
            await update_session_activity(request.session_id, target_server, None)

        # Broadcast command response to all connected WebSocket clients
        await broadcast_message({"type": "command_response", "data": response.dict()})
        
        return response
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        response = CommandResponse(
            command_id=command_id,
            status="error",
            error=str(e),
            timestamp=datetime.now(),
            execution_time=execution_time
        )
        
        command_history.append(response)
        await broadcast_message({"type": "command_error", "data": response.dict()})
        return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "anonymous"):
    await websocket.accept()
    websocket_connections[session_id] = websocket
    logger.info(f"WebSocket connected: {session_id}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message from {session_id}: {data}")
            # Here you can add logic to process incoming WebSocket messages
            # For example, routing commands received via WebSocket
            # await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        del websocket_connections[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        if session_id in websocket_connections:
            del websocket_connections[session_id]

async def broadcast_message(message: Dict):
    """Broadcasts a message to all connected WebSocket clients."""
    disconnected_clients = []
    for session_id, websocket in websocket_connections.items():
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            logger.warning(f"Failed to send message to {session_id}: {e}. Marking for removal.")
            disconnected_clients.append(session_id)
        except Exception as e:
            logger.error(f"Error broadcasting to {session_id}: {e}")
            disconnected_clients.append(session_id)
    
    for session_id in disconnected_clients:
        if session_id in websocket_connections:
            del websocket_connections[session_id]
            logger.info(f"Removed disconnected WebSocket client: {session_id}")

async def determine_target_server(command: str) -> Optional[str]:
    """Determines the target server based on the command."""
    command_map = {
        "file_system": "system",
        "process_management": "system",
        "application_launching": "system",
        "hardware_interaction": "system",
        "send_whatsapp_message": "communication",
        "send_email": "communication",
        "make_phone_call": "communication",
        "handle_message": "communication",
        "vscode_control": "ide",
        "git_operation": "ide",
        "edit_file": "ide",
        "code_analysis": "ide",
        "github_workflow": "github",
        "repository_operation": "github",
        "ci_cd_control": "github",
        "issue_management": "github",
        "speech_recognition": "voice_ui",
        "voice_command": "voice_ui",
        "gui_automation": "voice_ui",
        "screen_control": "voice_ui",
        "execute_python_code": "python",
        "web_search": "browser"
    }
    
    # Check for direct command mapping
    if command in command_map:
        return command_map[command]

    # Fallback to a default server if no specific mapping is found
    # This can be refined with more sophisticated NLP or a default server
    logger.warning(f"No direct target server found for command: {command}. Attempting to infer.")
    
    # Example of simple inference (can be expanded)
    if "file" in command or "directory" in command:
        return "system"
    if "git" in command or "code" in command:
        return "ide"
    if "whatsapp" in command or "email" in command or "message" in command:
        return "communication"
    if "github" in command or "repo" in command:
        return "github"
    if "voice" in command or "speech" in command or "ui" in command:
        return "voice_ui"
    if "python" in command or "script" in command:
        return "python"
    if "search" in command or "browse" in command:
        return "browser"

    logger.error(f"Could not determine target server for command: {command}")
    return None

async def send_command_to_server(server_name: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Sends a command to the specified server."""
    port = SERVER_PORTS.get(server_name)
    if not port:
        raise ValueError(f"Unknown server: {server_name}")
    
    url = f"http://localhost:{port}/command"
    payload = {"command": command, "parameters": parameters}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()  # Raise an exception for bad status codes
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error sending command to {server_name} ({url}): {e}")
            raise HTTPException(status_code=500, detail=f"Failed to communicate with {server_name} server: {e}")

async def monitor_server_health():
    """Periodically monitors the health of all registered servers."""
    while True:
        for server_name, port in SERVER_PORTS.items():
            url = f"http://localhost:{port}/health"
            status = "unknown"
            response_time = 0.0
            error = None
            try:
                start_time = datetime.now()
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as response:
                        response.raise_for_status()
                        status = "healthy"
                        response_time = (datetime.now() - start_time).total_seconds()
            except aiohttp.ClientError as e:
                status = "unhealthy"
                error = str(e)
                logger.warning(f"Health check failed for {server_name} ({url}): {e}")
            except asyncio.TimeoutError:
                status = "unhealthy"
                error = "timeout"
                logger.warning(f"Health check timed out for {server_name} ({url})")
            except Exception as e:
                status = "unhealthy"
                error = str(e)
                logger.error(f"Unexpected error during health check for {server_name} ({url}): {e}")
            
            server_health_cache[server_name] = ServerHealth(
                name=server_name,
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error=error
            )
        await asyncio.sleep(10) # Check every 10 seconds

@app.get("/command_history", response_model=List[CommandResponse])
async def get_command_history():
    """Retrieves the command execution history."""
    return command_history

@app.get("/server_health", response_model=Dict[str, ServerHealth])
async def get_server_health():
    """Retrieves the current health status of all monitored servers."""
    return server_health_cache

@app.post("/broadcast")
async def post_broadcast_message(message: Dict):
    """Endpoint to trigger a broadcast message to all connected WebSocket clients."""
    await broadcast_message(message)
    return {"status": "message broadcasted"}



@app.post("/sessions", response_model=SessionInfo)
async def create_session(request: Request, user_id: str = Depends(get_current_active_user), initial_data: Optional[Dict[str, Any]] = None):
    session_id = str(uuid.uuid4())
    session = request.app.state.app_context.create_user_session(user_id, session_id, initial_data)
    logger.info(f"Session {session_id} created for user {user_id}")
    return session

@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(request: Request, user_id: str = Depends(get_current_active_user)):
    return list(request.app.state.app_context.user_sessions.get(user_id, {}).values())

@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str, request: Request, user_id: str = Depends(get_current_active_user)):
    session = request.app.state.app_context.get_user_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.put("/sessions/{session_id}/activity", response_model=SessionInfo)
async def update_session_activity(session_id: str, request: Request, new_session_data: Optional[Dict[str, Any]] = None, user_id: str = Depends(get_current_active_user)):
    session = request.app.state.app_context.get_user_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    request.app.state.app_context.update_user_session(user_id, session_id, new_session_data)
    session.last_activity = datetime.now()
    return session

@app.delete("/sessions/{session_id}", status_code=204)
async def close_session(session_id: str, request: Request, user_id: str = Depends(get_current_active_user)):
    session = request.app.state.app_context.get_user_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    request.app.state.app_context.close_user_session(user_id, session_id)
    logger.info(f"Session {session_id} closed for user {user_id}")

@app.get("/servers", response_model=List[ServerHealth])
async def get_server_health():
    """Get health status of all servers"""
    return list(server_health_cache.values())

@app.post("/servers/{server_name}/health")
async def check_server_health(server_name: str):
    """Force health check for a specific server"""
    if server_name not in SERVER_PORTS:
        raise HTTPException(status_code=404, detail="Server not found")
    
    health = await check_server(server_name)
    server_health_cache[server_name] = health
    
    return health

@app.get("/commands/history")
async def get_command_history(limit: int = 100):
    """Get command execution history"""
    return command_history[-limit:]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle WebSocket messages
            if message.get("type") == "subscribe":
                # Subscribe to server health updates
                pass
            elif message.get("type") == "command":
                # Execute command via WebSocket
                request = CommandRequest(**message.get("data", {}))
                response = await execute_command(request)
                await websocket.send_text(json.dumps({
                    "type": "command_response",
                    "data": response.dict()
                }))
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

@app.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected clients"""
    await broadcast_to_websockets(message)
    return {"message": "Broadcast sent successfully"}

# Background tasks
async def monitor_server_health():
    """Continuously monitor server health"""
    while True:
        for server_name in SERVER_PORTS:
            try:
                health = await check_server(server_name)
                server_health_cache[server_name] = health
                
                # Broadcast health updates
                await broadcast_to_websockets({
                    "type": "health_update",
                    "server": server_name,
                    "health": health.dict()
                })
                
            except Exception as e:
                logger.error(f"Failed to check health for {server_name}: {e}")
                server_health_cache[server_name] = ServerHealth(
                    name=server_name,
                    status="error",
                    last_check=datetime.now(),
                    response_time=0.0,
                    error=str(e)
                )
        
        await asyncio.sleep(30)  # Check every 30 seconds

# Utility functions
async def check_server(server_name: str) -> ServerHealth:
    """Check health of a specific server"""
    port = SERVER_PORTS[server_name]
    start_time = datetime.now()
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(f"http://localhost:{port}/health") as response:
                if response.status == 200:
                    response_time = (datetime.now() - start_time).total_seconds()
                    return ServerHealth(
                        name=server_name,
                        status="healthy",
                        last_check=datetime.now(),
                        response_time=response_time
                    )
                else:
                    response_time = (datetime.now() - start_time).total_seconds()
                    return ServerHealth(
                        name=server_name,
                        status="degraded",
                        last_check=datetime.now(),
                        response_time=response_time,
                        error=f"HTTP {response.status}"
                    )
    except Exception as e:
        return ServerHealth(
            name=server_name,
            status="unavailable",
            last_check=datetime.now(),
            response_time=0.0,
            error=str(e)
        )

async def determine_target_server(command: str) -> Optional[str]:
    """Determine which server should handle a command based on keywords"""
    command = command.lower()
    
    # Command routing rules
    if any(word in command for word in ["python", "code", "execute", "run"]):
        return "python"
    elif any(word in command for word in ["browser", "web", "url", "open"]):
        return "browser"
    elif any(word in command for word in ["system", "file", "process", "cpu", "memory"]):
        return "system"
    elif any(word in command for word in ["chat", "message", "send", "broadcast"]):
        return "communication"
    elif any(word in command for word in ["ide", "format", "lint", "analyze"]):
        return "ide"
    elif any(word in command for word in ["github", "repo", "commit", "push", "pull"]):
        return "github"
    elif any(word in command for word in ["voice", "speak", "listen", "gui"]):
        return "voice_ui"
    
    return None

async def send_command_to_server(server_name: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Send command to specific server"""
    port = SERVER_PORTS[server_name]
    
    try:
        async with aiohttp.ClientSession() as session:
            # Determine endpoint based on server
            endpoint = await determine_endpoint(server_name, command)
            
            async with session.post(
                f"http://localhost:{port}{endpoint}",
                json=parameters,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Server returned {response.status}: {error_text}")
                    
    except Exception as e:
        raise Exception(f"Failed to communicate with {server_name}: {str(e)}")

async def determine_endpoint(server_name: str, command: str) -> str:
    """Determine the correct endpoint for a command on a specific server"""
    command = command.lower()
    
    endpoint_mapping = {
        "python": "/execute",
        "browser": "/navigate",
        "system": "/command",
        "communication": "/send",
        "ide": "/analyze",
        "github": "/repository/info",
        "voice_ui": "/voice/command"
    }
    
    return endpoint_mapping.get(server_name, "/")

async def update_session_activity(session_id: str, server_name: str, new_session_data: Optional[Dict[str, Any]] = None):
    """Update session activity"""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        session.last_activity = datetime.now()
        if server_name not in session.active_servers:
            session.active_servers.append(server_name)
        if new_session_data:
            session.session_data.update(new_session_data)

async def broadcast_to_websockets(message: Dict[str, Any]):
    """Broadcast message to all WebSocket connections"""
    for connection in websocket_connections[:]:
        try:
            await connection.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            if connection in websocket_connections:
                websocket_connections.remove(connection)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)