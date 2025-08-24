import pytest
from httpx import AsyncClient
from orchestrator_service import app

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
async def test_process_request_mock(async_client, monkeypatch):
    async def mock_process_request(*args, **kwargs):
        return {"status": "success", "response": "processed request"}
    monkeypatch.setattr("orchestrator_service.process_request", mock_process_request)

    response = await async_client.post("/process", json={
        "request_id": "req123",
        "session_id": "sess456",
        "command": "test_command",
        "parameters": {"param1": "value1"}
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "response": "processed request"}

@pytest.mark.asyncio
async def test_get_status_mock(async_client, monkeypatch):
    async def mock_get_status(*args, **kwargs):
        return {"status": "success", "task_status": "completed"}
    monkeypatch.setattr("orchestrator_service.get_status", mock_get_status)

    response = await async_client.get("/status/req123")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "task_status": "completed"}