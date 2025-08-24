import pytest
from httpx import AsyncClient
from github_actions_server import app

@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_run_workflow_mock(async_client, monkeypatch):
    async def mock_run_workflow(*args, **kwargs):
        return {"status": "success", "run_id": "12345", "message": "Workflow dispatched"}
    monkeypatch.setattr("github_actions_server.run_workflow", mock_run_workflow)

    response = await async_client.post("/github/workflow/run", json={
        "repo_owner": "test_owner",
        "repo_name": "test_repo",
        "workflow_id": "test_workflow.yml",
        "git_ref": "main",
        "inputs": {"key": "value"}
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "run_id": "12345", "message": "Workflow dispatched"}

@pytest.mark.asyncio
async def test_get_workflow_run_status_mock(async_client, monkeypatch):
    async def mock_get_workflow_run_status(*args, **kwargs):
        return {"status": "success", "run_status": "completed", "conclusion": "success"}
    monkeypatch.setattr("github_actions_server.get_workflow_run_status", mock_get_workflow_run_status)

    response = await async_client.get("/github/workflow/status", params={
        "repo_owner": "test_owner",
        "repo_name": "test_repo",
        "run_id": "12345"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "run_status": "completed", "conclusion": "success"}

@pytest.mark.asyncio
async def test_get_workflow_run_logs_mock(async_client, monkeypatch):
    async def mock_get_workflow_run_logs(*args, **kwargs):
        return {"status": "success", "logs": "workflow logs content"}
    monkeypatch.setattr("github_actions_server.get_workflow_run_logs", mock_get_workflow_run_logs)

    response = await async_client.get("/github/workflow/logs", params={
        "repo_owner": "test_owner",
        "repo_name": "test_repo",
        "run_id": "12345"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "logs": "workflow logs content"}