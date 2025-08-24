import pytest
from httpx import AsyncClient
from communication_server import app, Message, MessageAck, MessageQueue

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
async def test_send_message(async_client):
    message_data = {
        "id": "test_id_1",
        "sender": "test_sender",
        "recipient": "test_recipient",
        "type": "text",
        "payload": {"content": "Hello, world!"},
        "timestamp": "2023-01-01T12:00:00",
        "priority": 1
    }
    response = await async_client.post("/send", json=message_data)
    assert response.status_code == 200
    assert response.json()["status"] == "pending" or response.json()["status"] == "sent"
    assert response.json()["message_id"] == "test_id_1"

@pytest.mark.asyncio
async def test_broadcast_message(async_client):
    message_data = {
        "id": "broadcast_id_1",
        "sender": "test_sender",
        "recipient": "broadcast",
        "type": "text",
        "payload": {"content": "Broadcast message"},
        "timestamp": "2023-01-01T12:00:00",
        "priority": 1
    }
    response = await async_client.post("/broadcast", json=message_data)
    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["message_id"] == "broadcast_id_1"

@pytest.mark.asyncio
async def test_get_messages(async_client):
    # First, send a message to ensure there's something to retrieve
    message_data = {
        "id": "get_msg_id_1",
        "sender": "test_sender",
        "recipient": "test_get_recipient",
        "type": "text",
        "payload": {"content": "Message for retrieval"},
        "timestamp": "2023-01-01T12:00:00",
        "priority": 1
    }
    await async_client.post("/send", json=message_data)

    response = await async_client.get("/messages/test_get_recipient")
    assert response.status_code == 200
    assert len(response.json()["messages"]) > 0
    assert response.json()["messages"][0]["id"] == "get_msg_id_1"

@pytest.mark.asyncio
async def test_acknowledge_message(async_client):
    ack_data = {"message_id": "some_message_id", "status": "acknowledged"}
    response = await async_client.post("/message/ack", json=ack_data)
    assert response.status_code == 200
    assert response.json() == {"status": "acknowledged", "message_id": "some_message_id"}

# Note: WhatsApp and Email tests require external services and credentials.
# These are mock tests and would need proper setup for real integration testing.

@pytest.mark.asyncio
async def test_send_whatsapp_message_mock(async_client, monkeypatch):
    async def mock_launch(*args, **kwargs):
        class MockPage:
            async def goto(self, url): pass
            async def waitForSelector(self, selector, options=None): pass
            async def click(self, selector): pass
            async def type(self, selector, text): pass
            async def keyboard_press(self, key): pass
        class MockBrowser:
            async def newPage(self): return MockPage()
            async def close(self): pass
        return MockBrowser()

    monkeypatch.setattr("communication_server.launch", mock_launch)

    response = await async_client.post("/whatsapp/send_message", params={
        "recipient": "+1234567890",
        "message": "Test WhatsApp message"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "WhatsApp message sent"}

@pytest.mark.asyncio
async def test_send_email_mock(async_client, monkeypatch):
    def mock_smtp_send_message(*args, **kwargs): pass
    monkeypatch.setattr("smtplib.SMTP_SSL.send_message", mock_smtp_send_message)

    response = await async_client.post("/email/send", params={
        "sender_email": "test@example.com",
        "sender_password": "password",
        "recipient_email": "recipient@example.com",
        "subject": "Test Subject",
        "body": "Test Body"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Email sent successfully"}

@pytest.mark.asyncio
async def test_get_inbox_mock(async_client, monkeypatch):
    class MockIMAP4_SSL:
        def __init__(self, host): pass
        def login(self, user, password): pass
        def select(self, mailbox): pass
        def search(self, charset, *criteria): return 'OK', [b'1 2']
        def fetch(self, message_id, message_parts):
            if message_id == b'1':
                return 'OK', [(b'header', b'From: sender@example.com\nTo: receiver@example.com\nSubject: Test Email 1\nDate: Mon, 01 Jan 2023 12:00:00 +0000\n\nBody 1'), b'']
            if message_id == b'2':
                return 'OK', [(b'header', b'From: sender2@example.com\nTo: receiver2@example.com\nSubject: Test Email 2\nDate: Mon, 01 Jan 2023 13:00:00 +0000\n\nBody 2'), b'']
            return 'OK', []
        def logout(self): pass

    monkeypatch.setattr("imaplib.IMAP4_SSL", MockIMAP4_SSL)

    response = await async_client.get("/email/inbox", params={
        "email_address": "test@example.com",
        "password": "password",
        "num_emails": 2
    })
    assert response.status_code == 200
    assert len(response.json()["emails"]) == 2
    assert response.json()["emails"][0]["Subject"] == "Test Email 1"

@pytest.mark.asyncio
async def test_send_sms_mock(async_client, monkeypatch):
    class MockMessages:
        def create(self, to, from_, body): 
            class MockMessage: 
                sid = "SM123"
            return MockMessage()
    class MockClient:
        def __init__(self, sid, token): pass
        messages = MockMessages()
    monkeypatch.setattr("twilio.rest.Client", MockClient)

    response = await async_client.post("/phone/send_sms", params={
        "account_sid": "ACxxxx",
        "auth_token": "token",
        "from_number": "+15017122661",
        "to_number": "+15558675310",
        "message_body": "Test SMS"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message_sid": "SM123"}

@pytest.mark.asyncio
async def test_make_call_mock(async_client, monkeypatch):
    class MockCalls:
        def create(self, to, from_, url): 
            class MockCall: 
                sid = "CA123"
            return MockCall()
    class MockClient:
        def __init__(self, sid, token): pass
        calls = MockCalls()
    monkeypatch.setattr("twilio.rest.Client", MockClient)

    response = await async_client.post("/phone/make_call", params={
        "account_sid": "ACxxxx",
        "auth_token": "token",
        "from_number": "+15017122661",
        "to_number": "+15558675310",
        "twiml_url": "http://example.com/twiml"
    })
    assert response.status_code == 200
    assert response.json() == {"status": "success", "call_sid": "CA123"}