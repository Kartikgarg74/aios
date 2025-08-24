"""
Integration test configuration for MCP servers
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys
import time
from typing import Generator

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import all server apps
from servers.system_operations_server import app as system_app
from servers.communication_server import app as comm_app
from servers.ide_integration_server import app as ide_app
from servers.github_actions_server import app as github_app
from servers.voice_ui_server import app as voice_app

@pytest.fixture(scope="module")
def system_client() -> Generator:
    """Test client for System Operations Server"""
    with TestClient(system_app) as client:
        yield client

@pytest.fixture(scope="module")
def comm_client() -> Generator:
    """Test client for Communication Server"""
    with TestClient(comm_app) as client:
        yield client

@pytest.fixture(scope="module")
def ide_client() -> Generator:
    """Test client for IDE Integration Server"""
    with TestClient(ide_app) as client:
        yield client

@pytest.fixture(scope="module")
def github_client() -> Generator:
    """Test client for GitHub Actions Server"""
    with TestClient(github_app) as client:
        yield client

@pytest.fixture(scope="module")
def voice_client() -> Generator:
    """Test client for Voice/UI Server"""
    with TestClient(voice_app) as client:
        yield client

@pytest.fixture(scope="module")
def all_clients(system_client, comm_client, ide_client, github_client, voice_client) -> dict:
    """Dictionary of all test clients"""
    return {
        "system": system_client,
        "communication": comm_client,
        "ide": ide_client,
        "github": github_client,
        "voice": voice_client
    }

@pytest.fixture
def wait_for_services():
    """Wait for services to be ready"""
    def _wait_for_services(clients, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                for name, client in clients.items():
                    response = client.get("/health")
                    assert response.status_code == 200
                    assert response.json()["status"] == "healthy"
                return True
            except Exception:
                time.sleep(0.5)
        raise TimeoutError("Services not ready within timeout period")
    return _wait_for_services