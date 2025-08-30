from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Optional
import time
import uuid
import asyncio

app = FastAPI()
mcp = FastMCP(name="communication")
# Use FastAPI for websocket functionality
# The FastMCP instance will be used for other functionality
# Mount the FastMCP ASGI application under /mcp so both MCP tools and WebSockets are available
app.mount("/mcp", mcp)

class Message(BaseModel):
    id: str
    sender: str
    recipient: str
    content: str
    timestamp: float
    read: bool = False

class Contact(BaseModel):
    id: str
    name: str
    email: str
    last_contact: float

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# In-memory storage for demo purposes
messages_db: Dict[str, Message] = {}
contacts_db: Dict[str, Contact] = {}

@mcp.tool()
async def send_message(sender: str, recipient: str, content: str) -> Message:
    """Send a message to another user."""
    message_id = str(uuid.uuid4())
    message = Message(
        id=message_id,
        sender=sender,
        recipient=recipient,
        content=content,
        timestamp=time.time()
    )
    messages_db[message_id] = message
    
    # Notify recipient if connected
    await manager.send_personal_message(
        f"New message from {sender}: {content}",
        recipient
    )
    
    return message

@mcp.tool()
async def get_messages(user_id: str, limit: int = 100) -> List[Message]:
    """Get messages for a user, both sent and received."""
    user_messages = [
        msg for msg in messages_db.values() 
        if msg.sender == user_id or msg.recipient == user_id
    ]
    return sorted(user_messages, key=lambda x: x.timestamp, reverse=True)[:limit]

@mcp.tool()
async def add_contact(name: str, email: str) -> Contact:
    """Add a new contact to the user's address book."""
    contact_id = str(uuid.uuid4())
    contact = Contact(
        id=contact_id,
        name=name,
        email=email,
        last_contact=time.time()
    )
    contacts_db[contact_id] = contact
    return contact

@mcp.tool()
async def get_contacts() -> List[Contact]:
    """Get list of all contacts."""
    return list(contacts_db.values())

@mcp.tool()
async def mark_as_read(message_id: str) -> bool:
    """Mark a message as read."""
    if message_id in messages_db:
        messages_db[message_id].read = True
        return True
    return False

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages
            await manager.broadcast(f"Client {client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast(f"Client {client_id} disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)