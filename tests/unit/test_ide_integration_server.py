import pytest
from httpx import AsyncClient
from ide_integration_server import app

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
async def test_open_file_mock(async_client, monkeypatch):
    async def mock_open_file(*args, **kwargs):
        return {"status": "success", "content": "file content"}
    monkeypatch.setattr("ide_integration_server.open_file", mock_open_file)

    response = await async_client.post("/ide/file/open", json={
        "file_path": "/test/path/to/file.txt"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "content": "file content"}

@pytest.mark.asyncio
async def test_save_file_mock(async_client, monkeypatch):
    async def mock_save_file(*args, **kwargs):
        return {"status": "success"}
    monkeypatch.setattr("ide_integration_server.save_file", mock_save_file)

    response = await async_client.post("/ide/file/save", json={
        "file_path": "/test/path/to/file.txt",
        "content": "new file content"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

@pytest.mark.asyncio
async def test_run_command_mock(async_client, monkeypatch):
    async def mock_run_command(*args, **kwargs):
        return {"status": "success", "output": "command output"}
    monkeypatch.setattr("ide_integration_server.run_command", mock_run_command)

    response = await async_client.post("/ide/command/run", json={
        "command": "ls",
        "args": ["-l"]
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "output": "command output"}