#!/usr/bin/env python3
"""
Voice/UI Server (Port 8006)
Handles voice commands, GUI interactions, and user interface management
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import speech_recognition as sr
import pyttsx3
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice/UI Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for voice processing
voice_queue = queue.Queue()
recognizer = sr.Recognizer()
tts_engine = None
active_connections: List[WebSocket] = []

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    voice_engine_status: str
    active_websockets: int
    audio_devices: List[str]

class VoiceCommand(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None

class GUIAction(BaseModel):
    action: str
    parameters: Dict[str, Any]
    target: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    voice_engine_status: str
    active_websockets: int
    audio_devices: List[str]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Voice/UI server"""
    audio_devices = []
    try:
        # Get available audio devices
        import pyaudio
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            device = p.get_device_info_by_index(i)
            audio_devices.append(device['name'])
        p.terminate()
    except Exception:
        audio_devices = ["Audio system unavailable"]
    
    voice_status = "ready" if tts_engine else "initializing"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        voice_engine_status=voice_status,
        active_websockets=len(active_connections),
        audio_devices=audio_devices
    )

@app.post("/voice/command")
async def process_voice_command(command: VoiceCommand):
    """Process a voice command"""
    try:
        # Parse voice command
        response = await parse_voice_command(command.command, command.context)
        return {
            "status": "processed",
            "command": command.command,
            "response": response,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to process voice command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gui/action")
async def process_gui_action(action: GUIAction):
    """Process a GUI action"""
    try:
        result = await process_gui_action(action.action, action.parameters, action.target)
        return {
            "status": "processed",
            "action": action.action,
            "result": result,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to process GUI action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/listen")
async def start_voice_listening():
    """Start listening for voice commands"""
    try:
        # Start voice recognition in background
        threading.Thread(target=listen_for_voice, daemon=True).start()
        return {
            "status": "listening_started",
            "message": "Voice recognition started",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to start voice listening: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/speak")
async def text_to_speech(text: str):
    """Convert text to speech"""
    try:
        await speak_text(text)
        return {
            "status": "spoken",
            "text": text,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to convert text to speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gui/screens")
async def get_available_screens():
    """Get list of available GUI screens"""
    screens = [
        {
            "id": "dashboard",
            "name": "Dashboard",
            "description": "Main application dashboard",
            "icon": "home"
        },
        {
            "id": "chat",
            "name": "AI Chat",
            "description": "AI conversation interface",
            "icon": "message"
        },
        {
            "id": "settings",
            "name": "Settings",
            "description": "Application settings",
            "icon": "settings"
        },
        {
            "id": "voice",
            "name": "Voice Control",
            "description": "Voice command interface",
            "icon": "mic"
        },
        {
            "id": "system",
            "name": "System Monitor",
            "description": "System health and monitoring",
            "icon": "monitor"
        }
    ]
    return {"screens": screens}

@app.post("/gui/navigation")
async def navigate_to_screen(screen_id: str, parameters: Optional[Dict[str, Any]] = None):
    """Navigate to a specific screen"""
    try:
        # Validate screen exists
        available_screens = ["dashboard", "chat", "settings", "voice", "system"]
        if screen_id not in available_screens:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Broadcast navigation to all connected clients
        await broadcast_gui_event("navigation", {
            "screen": screen_id,
            "parameters": parameters or {}
        })
        
        return {"status": "success", "message": f"Navigated to {screen_id}"}
    except Exception as e:
        logger.error(f"Failed to navigate to screen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gui/elements/update")
async def update_gui_element(element_id: str, updates: Dict[str, Any]):
    """Update specific GUI elements"""
    try:
        # Broadcast update to all connected clients
        await broadcast_gui_event("element_update", {
            "element_id": element_id,
            "updates": updates
        })
        return {"status": "success", "message": f"Element {element_id} updated"}
    except Exception as e:
        logger.error(f"Failed to update GUI element: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gui/notification")
async def send_gui_notification(message: str, type: str = "info", duration: int = 5000):
    """Send a notification to the GUI"""
    try:
        # Broadcast notification to all connected clients
        await broadcast_gui_event("notification", {
            "message": message,
            "type": type,
            "duration": duration
        })
        return {"status": "success", "message": "Notification sent"}
    except Exception as e:
        logger.error(f"Failed to send GUI notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice/commands")
async def get_voice_commands():
    """Get list of available voice commands"""
    commands = [
        {
            "command": "open dashboard",
            "description": "Navigate to main dashboard",
            "action": "navigate",
            "target": "dashboard"
        },
        {
            "command": "start chat",
            "description": "Open AI chat interface",
            "action": "navigate",
            "target": "chat"
        },
        {
            "command": "show settings",
            "description": "Open settings panel",
            "action": "navigate",
            "target": "settings"
        },
        {
            "command": "system status",
            "description": "Get system health status",
            "action": "query",
            "target": "system"
        },
        {
            "command": "stop listening",
            "description": "Stop voice recognition",
            "action": "control",
            "target": "voice_off"
        }
    ]
    return {"commands": commands}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time GUI updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process WebSocket messages
            if message.get("type") == "gui_action":
                result = await process_gui_action(
                    message["action"],
                    message.get("parameters", {}),
                    message.get("target", "")
                )
                await websocket.send_text(json.dumps({
                    "type": "gui_response",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def parse_voice_command(command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse and process voice commands"""
    command = command.lower().strip()
    
    # Command mapping
    if "dashboard" in command or "home" in command:
        return {"action": "navigate", "target": "dashboard"}
    elif "chat" in command or "talk" in command:
        return {"action": "navigate", "target": "chat"}
    elif "settings" in command or "config" in command:
        return {"action": "navigate", "target": "settings"}
    elif "status" in command or "health" in command:
        return {"action": "query", "target": "system", "query": "health"}
    elif "stop" in command or "quit" in command:
        return {"action": "control", "target": "exit"}
    else:
        return {"action": "unknown", "message": "Command not recognized"}

async def process_gui_action(action: str, parameters: Dict[str, Any], target: str) -> Dict[str, Any]:
    """Process GUI actions"""
    if action == "navigate":
        return {"status": "success", "navigation": {"screen": target, "parameters": parameters}}
    elif action == "update":
        return {"status": "success", "update": {"target": target, "changes": parameters}}
    elif action == "query":
        return {"status": "success", "query": {"target": target, "result": "data"}}
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

async def broadcast_gui_event(event_type: str, data: Dict[str, Any]):
    """Broadcast events to all connected WebSocket clients"""
    message = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    for connection in active_connections[:]:
        try:
            await connection.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            if connection in active_connections:
                active_connections.remove(connection)

def listen_for_voice():
    """Background function for voice recognition"""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            logger.info("Voice recognition started")
            
            while True:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio)
                    logger.info(f"Voice command detected: {text}")
                    
                    # Add to processing queue
                    voice_queue.put(text)
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    logger.error(f"Voice recognition error: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to initialize voice recognition: {e}")

async def speak_text(text: str):
    """Convert text to speech"""
    try:
        global tts_engine
        if not tts_engine:
            tts_engine = pyttsx3.init()
        
        tts_engine.say(text)
        tts_engine.runAndWait()
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        # Fallback to system speech
        try:
            import subprocess
            subprocess.run(["say", text], check=True)
        except Exception:
            logger.error("All text-to-speech methods failed")

# Initialize TTS engine on startup
try:
    tts_engine = pyttsx3.init()
    logger.info("Text-to-speech engine initialized")
except Exception as e:
    logger.warning(f"Failed to initialize TTS engine: {e}")
    tts_engine = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)