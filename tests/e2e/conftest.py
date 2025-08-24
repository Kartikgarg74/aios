"""
End-to-end test configuration for MCP system
"""
import pytest
from playwright.sync_api import sync_playwright
import os
import time
from typing import Generator

@pytest.fixture(scope="session")
def browser():
    """Launch browser instance for E2E testing"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    """Create new browser page"""
    page = browser.new_page()
    yield page
    page.close()

@pytest.fixture(scope="session")
def server_url():
    """Base URL for the MCP system"""
    return "http://localhost:8000"  # Assuming frontend runs on port 8000

@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for services to be ready"""
    def _wait_for_services(timeout=30):
        # This would actually ping health endpoints
        # Placeholder for actual implementation
        time.sleep(1)
        return True
    return _wait_for_services