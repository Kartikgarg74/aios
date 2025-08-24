"""
Test suite for Voice/UI Server (Port 8006)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from servers.voice_ui_server import app, VoiceCommand, GUIAction

client = TestClient(app)

@pytest.fixture
def mock_voice_engine():
    with patch('servers.voice_ui_server.pyttsx3.init') as mock_init:
        mock_engine = MagicMock()
        mock_init.return_value = mock_engine
        yield mock_engine

@pytest.fixture
def mock_speech_recognition():
    with patch('servers.voice_ui_server.sr.Recognizer') as mock_rec:
        mock_recognizer = MagicMock()
        mock_rec.return_value = mock_recognizer
        yield mock_recognizer

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "voice_engine_status" in data
    assert "active_websockets" in data
    assert "audio_devices" in data

@patch('servers.voice_ui_server.process_voice_command')
def test_process_voice_command(mock_process):
    """Test processing voice commands"""
    mock_process.return_value = {"result": "success"}
    command = {"command": "open dashboard", "context": {"user": "test"}}
    response = client.post("/voice/command", json=command)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["command"] == "open dashboard"
    assert "timestamp" in data

@patch('servers.voice_ui_server.process_gui_action')
def test_process_gui_action(mock_process):
    """Test processing GUI actions"""
    mock_process.return_value = {"result": "success"}
    action = {"action": "navigate", "parameters": {"screen": "dashboard"}, "target": "main"}
    response = client.post("/gui/action", json=action)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["action"] == "navigate"
    assert "timestamp" in data

def test_start_voice_listening():
    """Test starting voice listening"""
    with patch('threading.Thread') as mock_thread:
        response = client.post("/voice/listen")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "listening_started"
        assert mock_thread.called

@patch('servers.voice_ui_server.speak_text')
def test_text_to_speech(mock_speak):
    """Test text to speech conversion"""
    mock_speak.return_value = None
    response = client.post("/voice/speak", json={"text": "Hello world"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "spoken"
    assert data["text"] == "Hello world"

def test_get_available_screens():
    """Test getting available GUI screens"""
    response = client.get("/gui/screens")
    assert response.status_code == 200
    data = response.json()
    assert "screens" in data
    assert len(data["screens"]) > 0

def test_get_voice_commands():
    """Test getting available voice commands"""
    response = client.get("/voice/commands")
    assert response.status_code == 200
    data = response.json()
    assert "commands" in data
    assert len(data["commands"]) > 0

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection"""
    with patch('servers.voice_ui_server.WebSocket') as mock_ws:
        mock_ws.return_value = MagicMock()
        await app.websocket("/ws")(mock_ws)
        mock_ws.accept.assert_called_once()


@patch('servers.voice_ui_server.broadcast_gui_event')
def test_navigate_to_screen(mock_broadcast):
    """Test screen navigation"""
    response = client.post("/gui/navigation", json={"screen_id": "dashboard"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "navigated"
    assert data["screen"] == "dashboard"
    
    mock_broadcast.assert_called_once()