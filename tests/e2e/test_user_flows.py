"""
End-to-end tests for MCP system user flows
"""
import pytest
from playwright.sync_api import expect
import time

# Test user flows through the complete system

def test_system_monitoring_flow(page, server_url, wait_for_services):
    """Test complete flow from dashboard to system monitoring"""
    wait_for_services()
    
    # Navigate to application
    page.goto(f"{server_url}/dashboard")
    
    # Verify dashboard loaded
    expect(page.get_by_text("System Dashboard")).to_be_visible()
    
    # Navigate to system monitoring
    page.get_by_role("button", name="System Monitor").click()
    expect(page.get_by_text("CPU Usage")).to_be_visible()
    
    # Verify system data is displayed
    expect(page.get_by_text("Memory")).to_be_visible()
    expect(page.get_by_text("Disk")).to_be_visible()
    expect(page.get_by_text("Network")).to_be_visible()
    
    # Refresh data
    page.get_by_role("button", name="Refresh").click()
    expect(page.get_by_text("Updating")).to_be_visible()
    expect(page.get_by_text("Updating")).not_to_be_visible(timeout=10000)

def test_voice_command_flow(page, server_url, wait_for_services):
    """Test voice command interaction flow"""
    wait_for_services()
    
    # Navigate to voice control
    page.goto(f"{server_url}/voice")
    expect(page.get_by_text("Voice Control")).to_be_visible()
    
    # Start listening
    page.get_by_role("button", name="Start Listening").click()
    expect(page.get_by_text("Listening")).to_be_visible()
    
    # Simulate voice command (in real test would use actual voice)
    page.get_by_test_id("voice-input").fill("open dashboard")
    page.get_by_role("button", name="Submit Command").click()
    
    # Verify navigation occurred
    expect(page).to_have_url(f"{server_url}/dashboard")

def test_ide_integration_flow(page, server_url, wait_for_services):
    """Test IDE integration through the UI"""
    wait_for_services()
    
    # Navigate to IDE integration
    page.goto(f"{server_url}/ide")
    expect(page.get_by_text("Code Analysis")).to_be_visible()
    
    # Enter code and analyze
    code = """def hello():
    print('Hello World')
"""
    page.get_by_label("Code Input").fill(code)
    page.get_by_role("button", name="Analyze").click()
    
    # Verify analysis results
    expect(page.get_by_text("Analysis Results")).to_be_visible()
    expect(page.get_by_text("Code Quality")).to_be_visible()
    
    # Verify suggestions
    expect(page.get_by_text("Suggestions")).to_be_visible()
    expect(page.get_by_text("print statement")).to_be_visible()

@pytest.mark.skip(reason="Requires GitHub credentials setup")
def test_github_actions_flow(page, server_url, wait_for_services):
    """Test GitHub actions through the UI"""
    wait_for_services()
    
    # Navigate to GitHub actions
    page.goto(f"{server_url}/github")
    expect(page.get_by_text("Repository Actions")).to_be_visible()
    
    # Select repository
    page.get_by_label("Repository").select_option("gpt-oss-mcp")
    
    # View workflows
    page.get_by_role("button", name="View Workflows").click()
    expect(page.get_by_text("Available Workflows")).to_be_visible()
    
    # Run workflow
    page.get_by_role("button", name="Run Tests").click()
    expect(page.get_by_text("Workflow Started")).to_be_visible()