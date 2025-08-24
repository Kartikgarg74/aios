"""
Test suite for System Operations Server
"""
import pytest
from fastapi.testclient import TestClient
from servers.system_operations_server import app
import os
import psutil

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "memory_usage" in data
    assert "cpu_usage" in data
    assert "disk_usage" in data

@pytest.mark.asyncio
async def test_system_info():
    """Test system info endpoint"""
    response = client.get("/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data

@pytest.mark.parametrize("command,args", [
    ("ls", ["-la"]),
    ("pwd", []),
    ("whoami", [])
])
def test_execute_command(command, args):
    """Test command execution endpoint"""
    response = client.post("/system/execute", json={
        "command": command,
        "args": args,
        "timeout": 30
    })
    assert response.status_code == 200
    data = response.json()
    assert "stdout" in data
    assert "stderr" in data
    assert "returncode" in data

def test_file_operations(tmp_path):
    """Test file operations"""
    test_file = tmp_path / "test_file.txt"
    
    # Create file
    response = client.post("/file/operation", json={
        "path": str(test_file),
        "operation": "create",
        "content": "test content"
    })
    assert response.status_code == 200
    assert os.path.exists(test_file)
    
    # Read file
    response = client.post("/file/operation", json={
        "path": str(test_file),
        "operation": "read"
    })
    assert response.status_code == 200
    assert "test content" in response.json()["content"]
    
    # Delete file
    response = client.post("/file/operation", json={
        "path": str(test_file),
        "operation": "delete"
    })
    assert response.status_code == 200
    assert not os.path.exists(test_file)

@pytest.mark.asyncio
async def test_process_management():
    """Test process management endpoints"""
    # Get processes
    response = client.get("/processes")
    assert response.status_code == 200
    data = response.json()
    assert "processes" in data
    assert "total" in data
    
    # Try to kill a process (should fail unless running as root)
    current_pid = os.getpid()
    response = client.post(f"/process/kill/{current_pid}")
    assert response.status_code in [403, 200]  # 403 if not root, 200 if root

@pytest.mark.parametrize("invalid_command", [
    "rm -rf /",
    "; rm -rf /",
    "| cat /etc/passwd"
])
def test_invalid_commands(invalid_command):
    """Test command validation"""
    response = client.post("/system/execute", json={
        "command": invalid_command,
        "args": [],
        "timeout": 30
    })
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

def test_invalid_file_operations():
    """Test path traversal protection"""
    response = client.post("/file/operation", json={
        "path": "/etc/passwd",
        "operation": "read"
    })
    assert response.status_code == 400
    assert "Path traversal detected" in response.json()["detail"]