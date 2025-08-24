"""
Basic security scan for MCP system
"""
import subprocess
import requests
import json

# Static analysis with Bandit
def run_bandit_scan(path):
    print(f"Running Bandit scan on {path}...")
    try:
        result = subprocess.run(
            ["bandit", "-r", path, "-f", "json"],
            capture_output=True, text=True, check=True
        )
        report = json.loads(result.stdout)
        print("Bandit Scan Results:")
        print(json.dumps(report, indent=2))
        return report
    except subprocess.CalledProcessError as e:
        print(f"Bandit scan failed: {e.stderr}")
        return None

# Simple API endpoint checks
import time

# Simple API endpoint checks
def check_api_endpoints(server_urls):
    print("Checking API endpoints...")
    results = {}
    for server_name, base_url in server_urls.items():
        print(f"  Checking {server_name} at {base_url}...")
        server_results = {}
        endpoints = {
            "health": f"{base_url}/health",
        }

        if server_name == "communication":
            endpoints.update({
                "send_message": (f"{base_url}/messages/send", {"sender": "test", "recipient": "test", "message": "hello"}, "post"),
                "whatsapp_send": (f"{base_url}/whatsapp/send_message", {"phone_number": "+1234567890", "message": "test"}, "post"),
                "email_send": (f"{base_url}/email/send", {"recipient": "test@example.com", "subject": "test", "body": "test"}, "post"),
                "phone_sms": (f"{base_url}/phone/send_sms", {"to": "+1234567890", "message": "test"}, "post"),
            })
        elif server_name == "system":
            endpoints.update({
                "list_usb": f"{base_url}/hardware/usb/list",
                "launch_app": (f"{base_url}/application/launch", {"app_name": "notepad"}, "post"),
                "read_file": (f"{base_url}/filesystem/read", {"file_path": "/etc/hosts"}, "post"),
            })
        elif server_name == "ide":
            endpoints.update({
                "open_file": (f"{base_url}/ide/file/open", {"file_path": "/tmp/test.txt"}, "post"),
            })
        elif server_name == "github":
            endpoints.update({
                "list_workflows": f"{base_url}/github/workflows",
            })
        elif server_name == "orchestrator":
            endpoints.update({
                "process_request": (f"{base_url}/process", {"request_id": "1", "session_id": "1", "command": "test", "parameters": {}}, "post"),
            })

        for name, config in endpoints.items():
            url = config[0] if isinstance(config, tuple) else config
            method = config[2] if isinstance(config, tuple) else "get"
            data = config[1] if isinstance(config, tuple) else None

            try:
                if method == "post":
                    response = requests.post(url, json=data, timeout=5)
                else:
                    response = requests.get(url, timeout=5)
                server_results[name] = {"status_code": response.status_code, "content_length": len(response.content)}
                print(f"    {name}: Status {response.status_code}, Length {len(response.content)}")
            except requests.exceptions.RequestException as e:
                server_results[name] = {"error": str(e)}
                print(f"    {name}: Error {e}")
        results[server_name] = server_results
    return results

def start_servers():
    print("Starting servers...")
    # This is a placeholder. In a real scenario, you would start each server process.
    # For example: subprocess.Popen(["python", "servers/communication_server.py"])
    # And then wait for them to be ready.
    server_processes = {}
    # Example for communication server (replace with actual paths and commands)
    # server_processes["communication"] = subprocess.Popen(["python", "./servers/communication_server.py"], env={"PORT": "8000"})
    # time.sleep(5) # Give server time to start
    print("Servers started (placeholder).")
    return server_processes

def stop_servers(server_processes):
    print("Stopping servers...")
    for name, proc in server_processes.items():
        proc.terminate()
        proc.wait()
    print("Servers stopped (placeholder).")

if __name__ == "__main__":
    # Run Bandit on the servers directory
    server_path = "./servers"
    bandit_report = run_bandit_scan(server_path)
    
    # Check common API endpoints
    # In a real scenario, you would start the servers here.
    # server_processes = start_servers()
    
    server_urls = {
        "communication": "http://localhost:8000",
        "system": "http://localhost:8002",
        "ide": "http://localhost:8003",
        "github": "http://localhost:8004",
        "voice": "http://localhost:8005",
        "orchestrator": "http://localhost:8006",
    }
    
    print("\n--- API Endpoint Checks ---")
    api_results = check_api_endpoints(server_urls)
    print("API Check Results:")
    print(json.dumps(api_results, indent=2))

    # In a real scenario, you would stop the servers here.
    # stop_servers(server_processes)