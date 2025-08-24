import pytest
from httpx import AsyncClient
from voice_ui_server import app

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
async def test_process_voice_command_mock(async_client, monkeypatch):
    async def mock_process_voice_command(*args, **kwargs):
        return {"status": "success", "response": "command processed"}
    monkeypatch.setattr("voice_ui_server.process_voice_command", mock_process_voice_command)

    response = await async_client.post("/voice/command", json={
        "command_text": "turn on lights"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "response": "command processed"}

@pytest.mark.asyncio
async def test_get_voice_response_mock(async_client, monkeypatch):
    async def mock_get_voice_response(*args, **kwargs):
        return {"status": "success", "audio_data": "base64encodedaudio"}
    monkeypatch.setattr("voice_ui_server.get_voice_response", mock_get_voice_response)

    response = await async_client.post("/voice/response", json={
        "text": "Hello, how can I help you?"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "audio_data": "base64encodedaudio"}