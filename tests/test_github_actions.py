"""
Test suite for GitHub Actions Server
"""
import pytest
from fastapi.testclient import TestClient
from servers.github_actions_server import app
from datetime import datetime
import json

client = TestClient(app)

# Mock GitHub API responses
MOCK_REPO_INFO = {
    "id": 123456,
    "name": "test-repo",
    "full_name": "owner/test-repo",
    "private": False
}

MOCK_WORKFLOWS = {
    "total_count": 2,
    "workflows": [
        {"id": 1, "name": "CI"},
        {"id": 2, "name": "CD"}
    ]
}

MOCK_WORKFLOW_RUNS = {
    "total_count": 3,
    "workflow_runs": [
        {"id": 1, "status": "completed"},
        {"id": 2, "status": "in_progress"},
        {"id": 3, "status": "queued"}
    ]
}

MOCK_BRANCHES = [
    {"name": "main", "commit": {"sha": "abc123"}},
    {"name": "dev", "commit": {"sha": "def456"}}
]

MOCK_PULL_REQUESTS = [
    {"id": 1, "title": "Feature 1", "state": "open"},
    {"id": 2, "title": "Bug fix", "state": "closed"}
]

def test_health_check(monkeypatch):
    """Test health check endpoint"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"status": "good"}
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_get)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "github_api_status" in data
    assert "active_workflows" in data

@pytest.mark.parametrize("mock_response,expected_count", [
    (MOCK_REPO_INFO, None),
    ({"message": "Not Found"}, 404)
])
def test_get_repository_info(monkeypatch, mock_response, expected_count):
    """Test repository info endpoint"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200 if expected_count is None else expected_count
            def json(self):
                return mock_response
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_get)
    
    test_data = {
        "token": "test_token",
        "repository": "test-repo",
        "owner": "owner"
    }
    
    response = client.post("/repository/info", json=test_data)
    
    if expected_count is None:
        assert response.status_code == 200
        assert response.json()["name"] == "test-repo"
    else:
        assert response.status_code == expected_count

@pytest.mark.parametrize("mock_response,expected_count", [
    (MOCK_WORKFLOWS, 2),
    ({"message": "Not Found"}, 404)
])
def test_list_workflows(monkeypatch, mock_response, expected_count):
    """Test workflows listing endpoint"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200 if isinstance(expected_count, int) else expected_count
            def json(self):
                return mock_response
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_get)
    
    test_data = {
        "token": "test_token",
        "repository": "test-repo",
        "owner": "owner"
    }
    
    response = client.post("/workflows/list", json=test_data)
    
    if isinstance(expected_count, int):
        assert response.status_code == 200
        assert response.json()["total_count"] == expected_count
    else:
        assert response.status_code == expected_count

@pytest.mark.parametrize("workflow_id,mock_response,expected_count", [
    (None, MOCK_WORKFLOW_RUNS, 3),
    ("123", MOCK_WORKFLOW_RUNS, 3),
    ("123", {"message": "Not Found"}, 404)
])
def test_get_workflow_runs(monkeypatch, workflow_id, mock_response, expected_count):
    """Test workflow runs endpoint"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200 if isinstance(expected_count, int) else expected_count
            def json(self):
                return mock_response
        return MockResponse()
    
    monkeypatch.setattr("requests.get", mock_get)
    
    test_data = {
        "token": "test_token",
        "repository": "test-repo",
        "owner": "owner"
    }
    
    params = {}
    if workflow_id:
        params["workflow_id"] = workflow_id
    
    response = client.post("/workflows/runs", json=test_data, params=params)
    
    if isinstance(expected_count, int):
        assert response.status_code == 200
        assert response.json()["total_count"] == expected_count
    else:
        assert response.status_code == expected_count

@pytest.mark.parametrize("mock_response,expected_status", [
    (None, 204),
    ({"message": "Not Found"}, 404)
])
def test_trigger_workflow(monkeypatch, mock_response, expected_status):
    """Test workflow triggering endpoint"""
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = expected_status
            def json(self):
                return mock_response or {}
        return MockResponse()
    
    monkeypatch.setattr("requests.post", mock_post)
    
    test_data = {
        "token": "test_token",
        "repository": "test-repo",
        "owner": "owner"
    }
    
    response = client.post("/workflows/trigger", json=test_data, params={"workflow_id": "123"})
    assert response.status_code == 200 if expected_status == 204 else expected_status

@pytest.mark.parametrize("workflow_config", [
    {"name": "CI", "on": {"push": {"branches": ["main"]}}, "jobs": {"build": {"runs-on": "ubuntu-latest", "steps": []}}},
    {"name": "Test", "on": "push", "jobs": {}}
])
def test_create_workflow(workflow_config):
    """Test workflow creation endpoint"""
    test_data = {
        "token": "test_token",
        "repository": "test-repo",
        "owner": "owner"
    }
    
    response = client.post("/workflows/create", json={"config": test_data, "workflow_config": workflow_config})
    assert response.status_code == 200
    assert "workflow_content" in response.json()
    assert "file_path" in response.json()
    assert workflow_config["name"] in response.json()["workflow_content"]