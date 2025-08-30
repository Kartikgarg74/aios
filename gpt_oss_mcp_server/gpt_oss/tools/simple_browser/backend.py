from typing import Dict, List, Optional, Any

# Import necessary libraries for browser automation
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    pass  # Handle gracefully if selenium is not installed

class ExaBackend:
    """
    Backend implementation for browser automation using Selenium.
    This class provides methods for web browsing, searching, and content extraction.
    """
    def __init__(self, source: str = "web"):
        """
        Initialize the ExaBackend with a specified source.
        
        Args:
            source: The source to use for browsing (e.g., "web", "local")
        """
        self.source = source
        self.current_page = None
        self.history = []
        self.driver = None
        
    def initialize_driver(self):
        """
        Initialize the Selenium WebDriver with Chrome if not already initialized.
        Sets up headless mode and other necessary options.
        """
        if self.driver is None:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Add user agent to avoid detection
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/91.0.4472.124 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=options)
    
    def close(self):
        """
        Close the WebDriver and clean up resources.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_page_content(self) -> Dict[str, Any]:
        """
        Extract content from the current page.
        
        Returns:
            A dictionary containing the page title, URL, and text content.
        """
        if not self.driver:
            return {"error": "Browser not initialized"}
        
        try:
            return {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "content": self.driver.find_element(By.TAG_NAME, "body").text
            }
        except Exception as e:
            return {"error": str(e)}
    
    def take_screenshot(self, path: Optional[str] = None) -> Optional[str]:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Optional path to save the screenshot to.
            
        Returns:
            The path where the screenshot was saved, or None if failed.
        """
        if not self.driver:
            return None
        
        try:
            if path:
                return self.driver.save_screenshot(path)
            else:
                # Return base64 encoded screenshot
                return self.driver.get_screenshot_as_base64()
        except Exception:
            return None