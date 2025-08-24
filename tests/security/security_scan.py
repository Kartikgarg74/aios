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
def check_api_endpoints(base_url):
    print(f"Checking API endpoints at {base_url}...")
    endpoints = {
        "health": f"{base_url}/health",
        "system_info": f"{base_url}/system/info",
        "file_read": f"{base_url}/system/file/read",
        "command_exec": f"{base_url}/system/command/execute"
    }
    
    results = {}
    for name, url in endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            results[name] = {"status_code": response.status_code, "content_length": len(response.content)}
            print(f"  {name}: Status {response.status_code}, Length {len(response.content)}")
        except requests.exceptions.RequestException as e:
            results[name] = {"error": str(e)}
            print(f"  {name}: Error {e}")
    
    return results

if __name__ == "__main__":
    # Run Bandit on the servers directory
    server_path = "./servers"
    bandit_report = run_bandit_scan(server_path)
    
    # Check common API endpoints (assuming servers are running)
    # You would typically run this against a deployed or local instance
    # For this example, we'll just show the structure
    print("\n--- API Endpoint Checks (Manual Run Required) ---")
    print("Please ensure your MCP servers are running before performing API checks.")
    # Example usage if servers were running:
    # system_server_url = "http://localhost:8002"
    # api_results = check_api_endpoints(system_server_url)
    # print("API Check Results:")
    # print(json.dumps(api_results, indent=2))