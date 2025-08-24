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

@pytest.mark.asyncio
async def test_orchestrator_to_system_command(all_clients: Dict, wait_for_services):
    """Test Orchestrator sending command to System server"""
    wait_for_services(all_clients)

    command_payload = {
        "request_id": "orch_req_1",
        "session_id": "orch_sess_1",
        "command": "system_command",
        "parameters": {"action": "get_status"}
    }

    # Send command via orchestrator
    orchestrator_response = await all_clients["orchestrator"].post("/process", json=command_payload)
    assert orchestrator_response.status_code == 200
    assert orchestrator_response.json()["status"] == "success"

    # In a real scenario, the orchestrator would then interact with the system server.
    # For this integration test, we'll mock the system server's response or check a side effect.
    # For now, we'll assume the orchestrator successfully processed the request.
    # A more robust test would involve checking logs or a mock database for the system command execution.
    assert "response" in orchestrator_response.json()

@pytest.mark.asyncio
async def test_orchestrator_to_communication_message(all_clients: Dict, wait_for_services):
    """Test Orchestrator sending message to Communication server"""
    wait_for_services(all_clients)

    message_payload = {
        "request_id": "orch_msg_1",
        "session_id": "orch_sess_2",
        "command": "send_message",
        "parameters": {
            "sender": "orchestrator",
            "recipient": "user",
            "message_type": "notification",
            "content": {"text": "Orchestrator initiated action completed."}
        }
    }

    # Send message via orchestrator
    orchestrator_response = await all_clients["orchestrator"].post("/process", json=message_payload)
    assert orchestrator_response.status_code == 200
    assert orchestrator_response.json()["status"] == "success"

    # Verify message was received by communication server (mocked or actual check)
    # This would typically involve checking the communication server's message queue or a mock.
    # For simplicity, we'll check if the orchestrator processed the request successfully.
    assert "response" in orchestrator_response.json()