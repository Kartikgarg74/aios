#!/usr/bin/env python3
"""
Communication Server (Port 8003)
Handles inter-server messaging and coordination between MCP servers
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Communication Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Message queue using Redis (fallback to in-memory)
class MessageQueue:
    def __init__(self):
        self.redis_client = None
        self.memory_queue = []
        self.subscribers = {}
        
    async def connect_redis(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory queue: {e}")
            self.redis_client = None
    
    async def publish_message(self, channel: str, message: Dict[str, Any]):
        if self.redis_client:
            await self.redis_client.publish(channel, json.dumps(message))
        else:
            self.memory_queue.append({"channel": channel, "message": message})
            await self.notify_subscribers(channel, message)
    
    async def subscribe(self, channel: str, callback):
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)

    async def unsubscribe(self, channel: str, callback):
        if channel in self.subscribers:
            self.subscribers[channel].remove(callback)
            if not self.subscribers[channel]:
                del self.subscribers[channel]

message_queue = MessageQueue()

# In-memory store for registered servers and active WebSocket connections
registered_servers: Dict[str, Dict[str, Any]] = {}
active_websocket_connections: Dict[str, WebSocket] = {}

class Message(BaseModel):
    id: str
    sender: str
    recipient: str
    type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    active_connections: int
    message_queue_size: int
    registered_servers_count: int

@app.on_event("startup")
async def startup_event():
    await message_queue.connect_redis()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for communication server"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        active_connections=len(active_websocket_connections),
        message_queue_size=len(message_queue.memory_queue),
        registered_servers_count=len(registered_servers)
    )

@app.post("/send")
async def send_message(message: Message):
    """Send a message between MCP servers"""
    try:
        if message.recipient in active_websocket_connections:
            await active_websocket_connections[message.recipient].send_json(message.dict())
            logger.info(f"Direct message sent to {message.recipient}")
        else:
            await message_queue.publish_message(
                f"messages:{message.recipient}",
                message.dict()
            )
            logger.info(f"Message published to Redis for {message.recipient}")
        return {"status": "sent", "message_id": message.id}
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{recipient}")
async def get_messages(recipient: str, limit: int = 100):
    """Get messages for a specific recipient"""
    try:
        messages = []
        if message_queue.redis_client:
            # Retrieve messages from a Redis list or stream for the recipient
            # For simplicity, let's assume a list for now
            key = f"messages_history:{recipient}"
            raw_messages = await message_queue.redis_client.lrange(key, -limit, -1)
            messages = [json.loads(msg) for msg in raw_messages]
            logger.info(f"Retrieved {len(messages)} messages from Redis for {recipient}")
        else:
            # In-memory implementation
            messages = [
                msg["message"] for msg in message_queue.memory_queue
                if msg["channel"] == f"messages:{recipient}"
            ]
            messages = messages[-limit:]  # Get last N messages
            logger.info(f"Retrieved {len(messages)} messages from in-memory for {recipient}")
        
        return {"messages": messages, "count": len(messages)}
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/broadcast")
async def broadcast_message(message: Message):
    """Broadcast a message to all MCP servers"""
    try:
        # Send to all active WebSocket connections
        for client_id, connection in active_websocket_connections.items():
            await connection.send_json(message.dict())
            logger.info(f"Broadcast message sent to active WebSocket: {client_id}")

        # Publish to Redis for other subscribers
        await message_queue.publish_message("broadcast", message.dict())
        logger.info("Broadcast message published to Redis")

        return {"status": "broadcast_sent", "message_id": message.id}
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    active_websocket_connections[client_id] = websocket
    logger.info(f"WebSocket connected: {client_id}. Total active: {len(active_websocket_connections)}")
    
    async def message_handler(message: Dict[str, Any]):
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            logger.warning(f"Could not send message to {client_id}, connection likely closed: {e}")
            await message_queue.unsubscribe("broadcast", message_handler)
            await message_queue.unsubscribe(f"messages:{client_id}", message_handler)
            if client_id in active_websocket_connections:
                del active_websocket_connections[client_id]

    # Subscribe to broadcast channel and personal channel
    await message_queue.subscribe("broadcast", message_handler)
    await message_queue.subscribe(f"messages:{client_id}", message_handler)
    
    try:
        while True:
            data = await websocket.receive_json()
            message = Message(**data)
            
            # Store message in Redis history for recipient
            if message_queue.redis_client:
                key = f"messages_history:{message.recipient}"
                await message_queue.redis_client.rpush(key, json.dumps(message.dict()))
                await message_queue.redis_client.ltrim(key, -1000, -1) # Keep last 1000 messages

            # Publish message to recipient's channel
            await message_queue.publish_message(
                f"messages:{message.recipient}",
                message.dict()
            )
            logger.info(f"Received and processed message for {message.recipient} from {client_id}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        await message_queue.unsubscribe("broadcast", message_handler)
        await message_queue.unsubscribe(f"messages:{client_id}", message_handler)
        if client_id in active_websocket_connections:
            del active_websocket_connections[client_id]
        logger.info(f"Cleaned up WebSocket for {client_id}. Total active: {len(active_websocket_connections)}")

@app.get("/status")
async def get_system_status():
    """Get status of all MCP servers"""
    try:
        # This would typically check all connected servers
        return {
            "servers": registered_servers,
            "active_websocket_connections": list(active_websocket_connections.keys()),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register")
async def register_server(server_info: Dict[str, Any]):
    """Register a new MCP server"""
    try:
        server_id = server_info.get("server_id")
        if not server_id:
            raise HTTPException(status_code=400, detail="server_id is required")

        registered_servers[server_id] = {
            "last_seen": datetime.now().isoformat(),
            **server_info
        }
        logger.info(f"Server registered: {server_id} - {server_info}")
        
        # Optionally, notify orchestrator or broadcast registration
        registration_message = {
            "id": f"register_{server_id}_{datetime.now().isoformat()}",
            "sender": "communication_server",
            "recipient": "central_orchestrator", # Assuming orchestrator listens for this
            "type": "server_registration",
            "payload": server_info,
            "timestamp": datetime.now().isoformat()
        }
        await message_queue.publish_message("broadcast", registration_message)

        return {"status": "registered", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to register server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect")
async def disconnect_server(server_id: str):
    """Deregister a server or mark it as disconnected"""
    try:
        if server_id in registered_servers:
            del registered_servers[server_id]
            logger.info(f"Server deregistered: {server_id}")
        
        if server_id in active_websocket_connections:
            # Close the WebSocket connection if it's still open
            await active_websocket_connections[server_id].close()
            del active_websocket_connections[server_id]
            logger.info(f"Closed and removed WebSocket for {server_id}")

        # Optionally, broadcast disconnection
        disconnection_message = {
            "id": f"disconnect_{server_id}_{datetime.now().isoformat()}",
            "sender": "communication_server",
            "recipient": "central_orchestrator",
            "type": "server_disconnection",
            "payload": {"server_id": server_id},
            "timestamp": datetime.now().isoformat()
        }
        await message_queue.publish_message("broadcast", disconnection_message)

        return {"status": "disconnected", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to disconnect server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
            "payload": server_info,
            "timestamp": datetime.now()
        }
        
        await message_queue.publish_message(
            "server_registrations",
            registration_message
        )
        
        return {"status": "registered", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to register server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)