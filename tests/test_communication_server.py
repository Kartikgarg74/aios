"""
Test suite for Communication Server
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect
from servers.communication_server import app, MessageQueue
import json
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def message_queue():
    """Fixture for message queue"""
    mq = MessageQueue()
    yield mq
    mq.memory_queue = []
    mq.subscribers = {}

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_connections" in data
    assert "message_queue_size" in data

@pytest.mark.asyncio
async def test_send_message(message_queue):
    """Test sending a message"""
    test_message = {
        "id": "test123",
        "sender": "test_sender",
        "recipient": "test_recipient",
        "type": "test",
        "payload": {"key": "value"},
        "timestamp": datetime.now().isoformat(),
        "priority": 1
    }
    
    response = client.post("/send", json=test_message)
    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["message_id"] == "test123"

@pytest.mark.asyncio
async def test_get_messages(message_queue):
    """Test retrieving messages"""
    # Add test messages
    test_message = {
        "channel": "messages:test_recipient",
        "message": {
            "id": "test123",
            "sender": "test_sender",
            "recipient": "test_recipient",
            "type": "test",
            "payload": {"key": "value"},
            "timestamp": datetime.now().isoformat(),
            "priority": 1
        }
    }
    message_queue.memory_queue.append(test_message)
    
    response = client.get("/messages/test_recipient")
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"] == "test123"

@pytest.mark.asyncio
async def test_broadcast_message(message_queue):
    """Test broadcasting a message"""
    test_message = {
        "id": "broadcast123",
        "sender": "test_sender",
        "recipient": "all",
        "type": "broadcast",
        "payload": {"key": "value"},
        "timestamp": datetime.now().isoformat(),
        "priority": 1
    }
    
    response = client.post("/broadcast", json=test_message)
    assert response.status_code == 200
    assert response.json()["status"] == "broadcast_sent"

@pytest.mark.asyncio
async def test_websocket_communication(message_queue):
    """Test WebSocket communication"""
    with client.websocket_connect("/ws/test_client") as websocket:
        # Test sending a message through websocket
        test_message = {
            "id": "ws123",
            "sender": "test_client",
            "recipient": "other_client",
            "type": "test",
            "payload": {"key": "value"},
            "timestamp": datetime.now().isoformat(),
            "priority": 1
        }
        websocket.send_json(test_message)
        
        # Test receiving a broadcast message
        await message_queue.publish_message(
            "broadcast",
            {
                "id": "broadcast123",
                "sender": "system",
                "recipient": "all",
                "type": "broadcast",
                "payload": {"key": "value"},
                "timestamp": datetime.now().isoformat(),
                "priority": 1
            }
        )
        data = websocket.receive_json()
        assert data["type"] == "broadcast"

@pytest.mark.asyncio
async def test_get_system_status():
    """Test getting system status"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert "timestamp" in data
    assert len(data["servers"]) == 7  # All MCP servers

@pytest.mark.asyncio
async def test_register_server():
    """Test server registration"""
    server_info = {
        "server_id": "test_server",
        "type": "test",
        "port": 9999,
        "status": "healthy"
    }
    
    response = client.post("/register", json=server_info)
    assert response.status_code == 200
    assert response.json()["status"] == "registered"
    assert response.json()["server_id"] == "test_server"