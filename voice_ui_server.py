from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import wave
import io
import uuid
import time

app = FastAPI()
mcp = FastMCP(name="voice_ui")
app.include_router(mcp.router)

class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    sample_width: int = 2  # 16-bit

class VoiceCommand(BaseModel):
    text: str
    confidence: float
    timestamp: float

class UIEvent(BaseModel):
    type: str
    data: Dict
    timestamp: float

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_buffers: Dict[str, bytes] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.audio_buffers[client_id] = b''

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]

    async def send_audio(self, audio_data: bytes, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_bytes(audio_data)

    async def send_ui_event(self, event: UIEvent, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(event.dict())

manager = ConnectionManager()

@mcp.tool()
async def process_voice_command(audio_data: bytes, config: AudioConfig) -> VoiceCommand:
    """Process audio data and return recognized voice command."""
    # In a real implementation, this would use a speech-to-text service
    # For demo purposes, we'll just return a mock response
    return VoiceCommand(
        text="Open the dashboard",
        confidence=0.95,
        timestamp=time.time()
    )

@mcp.tool()
async def text_to_speech(text: str, config: AudioConfig) -> bytes:
    """Convert text to speech audio."""
    # In a real implementation, this would use a text-to-speech service
    # For demo purposes, we'll return silent audio
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(config.channels)
            wav_file.setsampwidth(config.sample_width)
            wav_file.setframerate(config.sample_rate)
            wav_file.writeframes(b'\x00' * config.sample_rate * config.sample_width)  # 1 second of silence
        return wav_buffer.getvalue()

@mcp.tool()
async def send_ui_notification(title: str, message: str, duration: float = 5.0) -> bool:
    """Send a UI notification to all connected clients."""
    event = UIEvent(
        type="notification",
        data={"title": title, "message": message, "duration": duration},
        timestamp=time.time()
    )
    
    for client_id in manager.active_connections:
        await manager.send_ui_event(event, client_id)
    
    return True

@app.websocket("/ws/voice/{client_id}")
async def voice_websocket(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for voice communication."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_bytes()
            manager.audio_buffers[client_id] += data
            
            # Process audio in chunks (e.g., every 1 second of audio)
            if len(manager.audio_buffers[client_id]) >= 32000:  # 16kHz, 16-bit, mono = 1 second
                audio_chunk = manager.audio_buffers[client_id][:32000]
                manager.audio_buffers[client_id] = manager.audio_buffers[client_id][32000:]
                
                # Process the voice command
                command = await process_voice_command(
                    audio_chunk, 
                    AudioConfig()
                )
                
                # Send the recognized command back to the client
                await manager.send_ui_event(
                    UIEvent(
                        type="voice_command",
                        data=command.dict(),
                        timestamp=time.time()
                    ),
                    client_id
                )
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.websocket("/ws/ui/{client_id}")
async def ui_websocket(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for UI events."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle UI events from the client
            event = UIEvent(**data)
            
            # Broadcast to other clients if needed
            if event.type == "broadcast":
                for cid in manager.active_connections:
                    if cid != client_id:
                        await manager.send_ui_event(event, cid)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)