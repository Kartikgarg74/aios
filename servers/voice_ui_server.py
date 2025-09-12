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
import numpy as np
import tensorflow as tf

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

from shared.error_handling import configure_error_handling
configure_error_handling(app)

# Global variables for voice processing
voice_queue = queue.Queue()
recognizer = sr.Recognizer()
tts_engine = None
active_connections: List[WebSocket] = []

# TensorFlow Speech Recognition Model (Placeholder)
speech_model = None

async def load_speech_model():
    global speech_model
    try:
        # In a real application, this would load a pre-trained TensorFlow model
        # For demonstration, we'll just simulate a loaded model
        logger.info("Loading TensorFlow speech recognition model...")
        # speech_model = tf.keras.models.load_model("path/to/your/model")
        speech_model = True # Simulate successful loading
        logger.info("TensorFlow speech recognition model loaded.")
    except Exception as e:
        logger.error(f"Failed to load speech model: {e}")

@app.on_event("startup")
async def startup_event():
    await load_speech_model()

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
async def speak_text(text: str):
    """Converts text to speech and plays it."""
    try:
        logger.info(f"Converting text to speech: {text}")
        engine.say(text)
        engine.runAndWait()
        return {"status": "success", "message": "Text-to-speech completed"}
    except Exception as e:
        logger.error(f"Error during text-to-speech conversion: {e}")
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

@app.post("/gui/click")
async def click_gui(x: int, y: int):
    """Simulates a mouse click at the specified coordinates."""
    try:
        logger.info(f"Simulating click at x={x}, y={y}")
        # Placeholder for actual GUI click automation
        # pyautogui.click(x, y) # Requires pyautogui library
        return {"status": "success", "message": f"Clicked at ({x}, {y})"}
    except Exception as e:
        logger.error(f"Error simulating GUI click: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gui/type")
async def type_gui(text: str):
    """Simulates typing text."""
    try:
        logger.info(f"Simulating typing: {text}")
        # Placeholder for actual GUI typing automation
        # pyautogui.write(text) # Requires pyautogui library
        return {"status": "success", "message": f"Typed: {text}"}
    except Exception as e:
        logger.error(f"Error simulating GUI typing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gui/drag")
async def drag_gui(x: int, y: int, duration: float = 0.5):
    """Simulates dragging the mouse to a specified coordinate."""
    try:
        logger.info(f"Simulating drag to x={x}, y={y} over {duration} seconds")
        # Placeholder for actual GUI drag automation
        # pyautogui.dragTo(x, y, duration=duration) # Requires pyautogui library
        return {"status": "success", "message": f"Dragged to ({x}, {y})"}
    except Exception as e:
        logger.error(f"Error simulating GUI drag: {e}")
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

@app.post("/screen/screenshot")
async def capture_screenshot():
    """Captures a screenshot of the current screen and returns it as a base64 encoded string."""
    try:
        logger.info("Capturing screenshot...")
        # Placeholder for actual screenshot capture
        # screenshot = pyautogui.screenshot() # Requires pyautogui library
        # buffered = BytesIO()
        # screenshot.save(buffered, format="PNG")
        # img_str = base64.b64encode(buffered.getvalue()).decode()
        return {"status": "success", "message": "Screenshot captured (simulated)", "image": "base64_encoded_image_data"}
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/screen/record_start")
async def start_screen_record():
    """Starts recording the screen."""
    try:
        logger.info("Starting screen recording...")
        # Placeholder for actual screen recording start logic
        return {"status": "success", "message": "Screen recording started (simulated)"}
    except Exception as e:
        logger.error(f"Error starting screen recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/screen/record_stop")
async def stop_screen_record():
    """Stops recording the screen and returns the recorded video."""
    try:
        logger.info("Stopping screen recording...")
        # Placeholder for actual screen recording stop logic
        return {"status": "success", "message": "Screen recording stopped (simulated)", "video": "base64_encoded_video_data"}
    except Exception as e:
        logger.error(f"Error stopping screen recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _extract_parameters(command: str, pattern: str) -> Dict[str, Any]:
    """Extracts parameters from a command string based on a given pattern."""
    # This is a simplified example. A real implementation would use regex or a more advanced parser.
    params = {}
    if "open" in pattern and "application" in pattern:
        if "open" in command:
            app_name = command.replace("open", "").replace("application", "").strip()
            if app_name:
                params["application_name"] = app_name
    elif "search for" in pattern:
        if "search for" in command:
            query = command.replace("search for", "").strip()
            if query:
                params["query"] = query
    elif "open file" in pattern:
        if "open file" in command:
            file_path = command.replace("open file", "").strip()
            if file_path:
                params["file_path"] = file_path
    elif "create new file" in pattern:
        if "create new file" in command:
            file_name = command.replace("create new file", "").strip()
            if file_name:
                params["file_name"] = file_name
    elif "run command" in pattern:
        if "run command" in command:
            cmd = command.replace("run command", "").strip()
            if cmd:
                params["command"] = cmd
    return params


async def parse_voice_command(command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse and process voice commands"""
    command = command.lower().strip()

    command_patterns = {
        "open dashboard": {"action": "navigate", "target": "dashboard"},
        "start chat": {"action": "navigate", "target": "chat"},
        "show settings": {"action": "navigate", "target": "settings"},
        "system status": {"action": "query", "target": "system", "query": "health"},
        "stop listening": {"action": "control", "target": "voice_off"},
        "open application": {"action": "open_application"},
        "close application": {"action": "close_application"},
        "switch to": {"action": "switch_application"},
        "take screenshot": {"action": "capture_screen"},
        "read text": {"action": "text_to_speech"},
        "search for": {"action": "search_web"},
        "open file": {"action": "open_file"},
        "create new file": {"action": "create_file"},
        "run command": {"action": "run_terminal_command"},
        "save work": {"action": "save_work"},
    }

    for pattern, action_data in command_patterns.items():
        if pattern in command:
            parameters = await _extract_parameters(command, pattern)
            return {**action_data, **parameters}

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
    if not speech_model:
        logger.warning("Speech recognition model not loaded. Cannot listen for voice.")
        return

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            logger.info("Listening for voice command...")
            
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                    # Convert audio to a format suitable for TensorFlow model
                    # This is a placeholder for actual audio processing and model inference
                    audio_data = np.frombuffer(audio.frame_data, dtype=np.int16)
                    # Simulate processing with a TensorFlow model
                    # In a real scenario, you would pass audio_data to your speech_model
                    # For example: text = speech_model.predict(audio_data)
                    
                    # Simulate processing with a TensorFlow model
                    # In a real scenario, you would pass audio_data to your speech_model
                    # For example: predictions = speech_model.predict(np.expand_dims(audio_data, axis=0))
                    # text = decode_predictions(predictions) # A function to convert model output to text
                    text = "Simulated TensorFlow recognition: This is a test command."
                    logger.info(f"Recognized (TensorFlow simulated): {text}")
                    
                    # Add to processing queue
                    voice_queue.put(text)
                    
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    logger.warning("Could not understand audio")
                    continue
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service; {e}")
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