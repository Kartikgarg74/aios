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
        self.client.post("/whatsapp/send_message", json={
            "phone_number": "+1234567890",
            "message": "Hello from Locust!"
        })
        self.client.post("/email/send", json={
            "recipient": "test@example.com",
            "subject": "Locust Test Email",
            "body": "This is a test email from Locust."
        })
        self.client.post("/phone/send_sms", json={
            "to": "+1234567890",
            "message": "Locust SMS Test"
        })
    
    @task(1)
    def voice_commands(self):
        """Test voice command processing"""
        self.client.post("/voice/command", json={
            "command": "open dashboard",
            "context": {"user": "test"}
        })

    @task(2)
    def orchestrator_requests(self):
        """Test orchestrator service endpoints"""
        self.client.post("/orchestrator/process", json={
            "request_id": "locust_orch_req",
            "session_id": "locust_orch_sess",
            "command": "test_command",
            "parameters": {"param1": "value1"}
        })
        self.client.get("/orchestrator/status/locust_orch_req")