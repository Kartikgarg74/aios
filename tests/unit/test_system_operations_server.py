import pytest
from httpx import AsyncClient
from system_operations_server import app

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
async def test_list_usb_devices_mock(async_client, monkeypatch):
    async def mock_list_usb_devices(*args, **kwargs):
        return {"status": "success", "devices": ["device1", "device2"]}
    monkeypatch.setattr("system_operations_server.list_usb_devices", mock_list_usb_devices)

    response = await async_client.get("/hardware/usb/list")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "devices": ["device1", "device2"]}

@pytest.mark.asyncio
async def test_launch_application_mock(async_client, monkeypatch):
    async def mock_launch_application(*args, **kwargs):
        return {"status": "success", "pid": 1234}
    monkeypatch.setattr("system_operations_server.launch_application", mock_launch_application)

    response = await async_client.post("/application/launch", json={
        "app_name": "test_app",
        "args": ["--test"]
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "pid": 1234}

@pytest.mark.asyncio
async def test_read_file_mock(async_client, monkeypatch):
    async def mock_read_file(*args, **kwargs):
        return {"status": "success", "content": "file content"}
    monkeypatch.setattr("system_operations_server.read_file", mock_read_file)

    response = await async_client.post("/filesystem/read", json={
        "file_path": "/test/path/to/file.txt"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "content": "file content"}

@pytest.mark.asyncio
async def test_get_cpu_usage_mock(async_client, monkeypatch):
    async def mock_get_cpu_usage(*args, **kwargs):
        return {"status": "success", "cpu_percent": 50.5}
    monkeypatch.setattr("system_operations_server.get_cpu_usage", mock_get_cpu_usage)

    response = await async_client.get("/system/cpu_usage")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "cpu_percent": 50.5}