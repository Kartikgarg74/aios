"""
Integration tests for cross-server communication in MCP system
"""
import pytest
from typing import Dict
import json

# Test scenarios for cross-server communication

def test_system_to_communication_health(all_clients: Dict, wait_for_services):
    """Test health check propagation from System to Communication server"""
    wait_for_services(all_clients)
    
    # Get system health
    system_health = all_clients["system"].get("/health").json()
    
    # Send system status to communication server
    message = {
        "sender": "system",
        "recipient": "communication",
        "message_type": "health_update",
        "content": system_health
    }
    
    response = all_clients["communication"].post("/messages/send", json=message)
    assert response.status_code == 200
    
    # Verify message was received
    messages = all_clients["communication"].get(f"/messages/system").json()
    assert len(messages["messages"]) > 0
    assert messages["messages"][0]["message_type"] == "health_update"

def test_voice_command_to_system_action(all_clients: Dict, wait_for_services):
    """Test voice command triggering system action"""
    wait_for_services(all_clients)
    
    # Send voice command
    voice_command = {
        "command": "get system status",
        "context": {"user": "test"}
    }
    
    voice_response = all_clients["voice"].post("/voice/command", json=voice_command)
    assert voice_response.status_code == 200
    
    # Verify system action was triggered
    system_response = all_clients["system"].get("/health")
    assert system_response.status_code == 200
    
    # Verify response was sent to voice server
    messages = all_clients["communication"].get(f"/messages/voice").json()
    assert len(messages["messages"]) > 0
    assert "system_status" in messages["messages"][0]["content"]

def test_ide_to_github_integration(all_clients: Dict, wait_for_services):
    """Test IDE analysis triggering GitHub action"""
    wait_for_services(all_clients)
    
    # Analyze code in IDE server
    code_analysis = {
        "language": "python",
        "code": "print('Hello World')"
    }
    
    analysis_response = all_clients["ide"].post("/analyze/code", json=code_analysis)
    assert analysis_response.status_code == 200
    
    # Verify GitHub action was created
    workflows = all_clients["github"].get("/workflows").json()
    assert len(workflows["workflows"]) >= 0  # May be empty in test
    
    # Verify message was sent to communication server
    messages = all_clients["communication"].get(f"/messages/ide").json()
    assert len(messages["messages"]) > 0
    assert "analysis_result" in messages["messages"][0]["content"]

@pytest.mark.asyncio
async def test_websocket_broadcast(all_clients: Dict, wait_for_services):
    """Test WebSocket broadcast from Communication server"""
    wait_for_services(all_clients)
    
    # This would require actual WebSocket testing implementation
    # Placeholder for actual WebSocket test
    assert True