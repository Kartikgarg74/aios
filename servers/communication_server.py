#!/usr/bin/env python3
"""
Communication Server (Port 8003)
Handles inter-server messaging and coordination between MCP servers
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from loguru import logger
from pyppeteer import launch
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
from twilio.rest import Client

from logging_config import setup_logger, ServiceMonitor

from mcp.server import FastMCP

# Configure logging
logger = setup_logger("communication_server")

app = FastAPI(title="Communication Server", version="1.0.0")
mcp = FastMCP()

# Initialize ServiceMonitor
monitor = ServiceMonitor("communication_server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Message queue using Redis (fallback to in-memory)
class MessageQueue:
    def __init__(self):
        self.redis_client = None
        self.memory_queue = []
        self.subscribers = {}
        
    async def connect_redis(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory queue: {e}")
            self.redis_client = None
    
    async def publish_message(self, channel: str, message: Dict[str, Any]):
        message_obj = Message(**message)
        if self.redis_client:
            # Store message in a pending queue or hash for tracking
            await self.redis_client.hset(f"pending_messages:{message_obj.recipient}", message_obj.id, json.dumps(message_obj.dict()))
            await self.redis_client.publish(channel, json.dumps(message_obj.dict()))
        else:
            self.memory_queue.append({"channel": channel, "message": message_obj.dict()})
            await self.notify_subscribers(channel, message_obj.dict())
    
    async def subscribe(self, channel: str, callback):
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)

    async def unsubscribe(self, channel: str, callback):
        if channel in self.subscribers:
            self.subscribers[channel].remove(callback)
            if not self.subscribers[channel]:
                del self.subscribers[channel]

message_queue = MessageQueue()

# In-memory store for registered servers and active WebSocket connections
registered_servers: Dict[str, Dict[str, Any]] = {}
active_websocket_connections: Dict[str, WebSocket] = {}

class Message(BaseModel):
    id: str
    sender: str
    recipient: str
    type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1
    status: str = "pending"  # pending, sent, delivered, acknowledged, failed
    retries: int = 0

class MessageAck(BaseModel):
    message_id: str
    status: str = "acknowledged"

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    active_connections: int
    message_queue_size: int
    registered_servers_count: int

@app.on_event("startup")
async def startup_event():
    await message_queue.connect_redis()
    asyncio.create_task(retry_undelivered_messages())

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for communication server"""
    monitor.record_request()
    monitor.record_success()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        active_connections=len(active_websocket_connections),
        message_queue_size=len(message_queue.memory_queue),
        registered_servers_count=len(registered_servers)
    )

@app.post("/send")
async def send_message(message: Message):
    """Send a message between MCP servers"""
    monitor.record_request()
    try:
        message.timestamp = datetime.now()
        message.status = "pending"
        if message.recipient in active_websocket_connections:
            # For direct WebSocket, we assume it's sent immediately
            await active_websocket_connections[message.recipient].send_json(message.dict())
            message.status = "sent"
            logger.info(f"Direct message sent to {message.recipient}")
        
        await message_queue.publish_message(
            f"messages:{message.recipient}",
            message.dict()
        )
        logger.info(f"Message published to Redis for {message.recipient}")
        monitor.record_success()
        return {"status": message.status, "message_id": message.id}
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
async def send_sms(account_sid: str, auth_token: str, from_number: str, to_number: str, message_body: str):
    """Send an SMS message using Twilio."""
    monitor.record_request()
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            to=to_number,
            from_=from_number,
            body=message_body
        )
        logger.info(f"SMS sent to {to_number} with SID: {message.sid}")
        monitor.record_success()
        return {"status": "success", "message_sid": message.sid}
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
async def make_call(account_sid: str, auth_token: str, from_number: str, to_number: str, twiml_url: str):
    """Make a phone call using Twilio."""
    monitor.record_request()
    try:
        client = Client(account_sid, auth_token)
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=twiml_url  # URL to TwiML instructions for the call
        )
        logger.info(f"Call initiated to {to_number} with SID: {call.sid}")
        monitor.record_success()
        return {"status": "success", "call_sid": call.sid}
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to make call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{recipient}")
async def get_messages(recipient: str, limit: int = 100):
    """Get messages for a specific recipient"""
    try:
        messages = []
        if message_queue.redis_client:
            # Retrieve messages from a Redis list or stream for the recipient
            # For simplicity, let's assume a list for now
            key = f"messages_history:{recipient}"
            raw_messages = await message_queue.redis_client.lrange(key, -limit, -1)
            messages = [json.loads(msg) for msg in raw_messages]
            logger.info(f"Retrieved {len(messages)} messages from Redis for {recipient}")
        else:
            # In-memory implementation
            messages = [
                msg["message"] for msg in message_queue.memory_queue
                if msg["channel"] == f"messages:{recipient}"
            ]
            messages = messages[-limit:]  # Get last N messages
            logger.info(f"Retrieved {len(messages)} messages from in-memory for {recipient}")
        
        return {"messages": messages, "count": len(messages)}
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/broadcast")
async def broadcast_message(message: Message):
    """Broadcast a message to all MCP servers"""
    try:
        # Send to all active WebSocket connections
        for client_id, connection in active_websocket_connections.items():
            await connection.send_json(message.dict())
            logger.info(f"Broadcast message sent to active WebSocket: {client_id}")

        # Publish to Redis for other subscribers
        await message_queue.publish_message("broadcast", message.dict())
        logger.info("Broadcast message published to Redis")

        return {"status": "broadcast_sent", "message_id": message.id}
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    active_websocket_connections[client_id] = websocket
    logger.info(f"WebSocket connected: {client_id}. Total active: {len(active_websocket_connections)}")
    
    async def message_handler(message: Dict[str, Any]):
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            logger.warning(f"Could not send message to {client_id}, connection likely closed: {e}")
            await message_queue.unsubscribe("broadcast", message_handler)
            await message_queue.unsubscribe(f"messages:{client_id}", message_handler)
            if client_id in active_websocket_connections:
                del active_websocket_connections[client_id]

    # Subscribe to broadcast channel and personal channel
    await message_queue.subscribe("broadcast", message_handler)
    await message_queue.subscribe(f"messages:{client_id}", message_handler)
    
    try:
        while True:
            data = await websocket.receive_json()
            message = Message(**data)
            
            # Store message in Redis history for recipient and mark as delivered
            if message_queue.redis_client:
                key = f"messages_history:{message.recipient}"
                message.status = "delivered"
                await message_queue.redis_client.rpush(key, json.dumps(message.dict()))
                await message_queue.redis_client.ltrim(key, -1000, -1) # Keep last 1000 messages
                # Remove from pending messages once delivered
                await message_queue.redis_client.hdel(f"pending_messages:{message.recipient}", message.id)

            # Publish message to recipient's channel
            await message_queue.publish_message(
                f"messages:{message.recipient}",
                message.dict()
            )
            logger.info(f"Received and processed message for {message.recipient} from {client_id}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        await message_queue.unsubscribe("broadcast", message_handler)
        await message_queue.unsubscribe(f"messages:{client_id}", message_handler)
        if client_id in active_websocket_connections:
            del active_websocket_connections[client_id]
        logger.info(f"Cleaned up WebSocket for {client_id}. Total active: {len(active_websocket_connections)}")

@app.get("/status")
async def get_system_status():
    """Get status of all MCP servers"""
    try:
        # This would typically check all connected servers
        return {
            "servers": registered_servers,
            "active_websocket_connections": list(active_websocket_connections.keys()),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register")
async def register_server(server_info: Dict[str, Any]):
    """Register a new MCP server"""
    try:
        server_id = server_info.get("server_id")
        if not server_id:
            raise HTTPException(status_code=400, detail="server_id is required")

        registered_servers[server_id] = {
            "last_seen": datetime.now().isoformat(),
            **server_info
        }
        logger.info(f"Server registered: {server_id} - {server_info}")
        
        # Optionally, notify orchestrator or broadcast registration
        registration_message = {
            "id": f"register_{server_id}_{datetime.now().isoformat()}",
            "sender": "communication_server",
            "recipient": "central_orchestrator", # Assuming orchestrator listens for this
            "type": "server_registration",
            "payload": server_info,
            "timestamp": datetime.now().isoformat()
        }
        await message_queue.publish_message("broadcast", registration_message)

        return {"status": "registered", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to register server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect")
async def disconnect_server(server_id: str):
    """Deregister a server or mark it as disconnected"""
    try:
        if server_id in registered_servers:
            del registered_servers[server_id]
            logger.info(f"Server deregistered: {server_id}")
        
        if server_id in active_websocket_connections:
            # Close the WebSocket connection if it's still open
            await active_websocket_connections[server_id].close()
            del active_websocket_connections[server_id]
            logger.info(f"Closed and removed WebSocket for {server_id}")

        # Optionally, broadcast disconnection
        disconnection_message = {
            "id": f"disconnect_{server_id}_{datetime.now().isoformat()}",
            "sender": "communication_server",
            "recipient": "central_orchestrator",
            "type": "server_disconnection",
            "payload": {"server_id": server_id},
            "timestamp": datetime.now().isoformat()
        }
        await message_queue.publish_message("broadcast", disconnection_message)

        return {"status": "disconnected", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to disconnect server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

        
        await message_queue.publish_message(
            "server_registrations",
            registration_message
        )
        
        return {"status": "registered", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to register server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/message/ack")
async def acknowledge_message(ack: MessageAck):
    """Endpoint for clients to acknowledge message receipt."""
    if message_queue.redis_client:
        # Remove message from pending queue
        await message_queue.redis_client.hdel(f"pending_messages:{ack.status}", ack.message_id)
        logger.info(f"Message {ack.message_id} acknowledged and removed from pending.")
    return {"status": "acknowledged", "message_id": ack.message_id}

@mcp.tool()
async def send_whatsapp_message(recipient: str, message: str):
    """Send a WhatsApp message using Puppeteer."""
    browser = None
    try:
        browser = await launch(headless=True)  # Set to False for visual debugging
        page = await browser.newPage()
        await page.goto("https://web.whatsapp.com/")

        # Wait for WhatsApp Web to load and QR code to disappear (you might need to scan it manually first)
        await page.waitForSelector('._1JnLS', {'timeout': 60000})  # Selector for chat list

        # Search for the recipient
        await page.click('._2_F54')  # Click search icon
        await page.type('._2_F54 ._3FRCZ', recipient) # Type recipient name
        await page.waitForSelector(f'span[title="{recipient}"]')
        await page.click(f'span[title="{recipient}"]')

        # Type and send the message
        await page.waitForSelector('._1UWac ._3FRCZ') # Selector for message input box
        await page.type('._1UWac ._3FRCZ', message)
        await page.keyboard.press('Enter')

        logger.info(f"WhatsApp message sent to {recipient}")
        return {"status": "success", "message": "WhatsApp message sent"}
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if browser:
            await browser.close()

@mcp.tool()
async def send_email(sender_email: str, sender_password: str, recipient_email: str, subject: str, body: str):
    """Send an email via SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        logger.info(f"Email sent from {sender_email} to {recipient_email}")
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
async def get_inbox(email_address: str, password: str, num_emails: int = 5):
    """Retrieve emails from IMAP inbox."""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_address, password)
        mail.select('inbox')

        status, email_ids = mail.search(None, 'ALL')
        email_id_list = email_ids[0].split()
        latest_emails = email_id_list[-num_emails:]

        emails = []
        for email_id in latest_emails:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    email_info = {
                        "From": msg['from'],
                        "To": msg['to'],
                        "Subject": msg['subject'],
                        "Date": msg['date'],
                        "Body": ""
                    }
                    if msg.is_multipart():
                        for part in msg.walk():
                            ctype = part.get_content_type()
                            cdisposition = str(part.get("Content-Disposition"))

                            if ctype == 'text/plain' and 'attachment' not in cdisposition:
                                email_info["Body"] = part.get_payload(decode=True).decode()
                                break
                    else:
                        email_info["Body"] = msg.get_payload(decode=True).decode()
                    emails.append(email_info)
        mail.logout()
        logger.info(f"Retrieved {len(emails)} emails for {email_address}")
        return {"status": "success", "emails": emails}
    except Exception as e:
        logger.error(f"Failed to retrieve emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/mcp", mcp)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)