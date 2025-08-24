"""
Performance testing for MCP system using Locust
"""
from locust import HttpUser, task, between
import random

class MCPUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        """Test health check endpoints"""
        servers = ["system", "communication", "ide", "github", "voice"]
        server = random.choice(servers)
        self.client.get(f"/{server}/health")
    
    @task(2)
    def system_operations(self):
        """Test system operations endpoints"""
        self.client.get("/system/info")
        self.client.get("/system/processes")
    
    @task(2)
    def communication(self):
        """Test communication endpoints"""
        self.client.post("/messages/send", json={
            "sender": "test",
            "recipient": "system",
            "message": "test"
        })
    
    @task(1)
    def voice_commands(self):
        """Test voice command processing"""
        self.client.post("/voice/command", json={
            "command": "open dashboard",
            "context": {"user": "test"}
        })