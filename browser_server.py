from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Union, Optional, Dict, Any

from fastmcp import Context, FastMCP

# Import necessary libraries for browser automation
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    pass  # Handle gracefully if selenium is not installed

# Backend implementation for browser automation
class ExaBackend:
    def __init__(self, source: str = "web"):
        self.source = source
        self.current_page = None
        self.history = []
        self.driver = None
        
    def initialize_driver(self):
        if self.driver is None:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=options)
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

# Define the SimpleBrowserTool class
class SimpleBrowserTool:
    def __init__(self, backend=None):
        self.backend = backend if backend else ExaBackend()
        
    async def search(self, query: str) -> Dict[str, Any]:
        """Search the web for the given query."""
        self.backend.initialize_driver()
        try:
            self.backend.driver.get(f"https://www.google.com/search?q={query}")
            WebDriverWait(self.backend.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            results = self.backend.driver.find_elements(By.CSS_SELECTOR, "div.g")
            search_results = []
            for result in results[:5]:  # Limit to top 5 results
                try:
                    title = result.find_element(By.CSS_SELECTOR, "h3").text
                    link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    snippet = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text
                    search_results.append({"title": title, "link": link, "snippet": snippet})
                except Exception:
                    continue
            return {"results": search_results}
        finally:
            self.backend.close()
    
    async def open(self, url: str) -> Dict[str, Any]:
        """Open a specific URL and return its content."""
        self.backend.initialize_driver()
        try:
            self.backend.driver.get(url)
            WebDriverWait(self.backend.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            content = self.backend.driver.find_element(By.TAG_NAME, "body").text
            title = self.backend.driver.title
            return {"title": title, "content": content, "url": url}
        finally:
            self.backend.close()
    
    async def find(self, url: str, selector: str) -> Dict[str, Any]:
        """Find elements on a page using CSS selector."""
        self.backend.initialize_driver()
        try:
            self.backend.driver.get(url)
            WebDriverWait(self.backend.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            elements = self.backend.driver.find_elements(By.CSS_SELECTOR, selector)
            results = []
            for element in elements:
                results.append({"text": element.text, "html": element.get_attribute("outerHTML")})
            return {"elements": results, "count": len(results)}
        finally:
            self.backend.close()


@dataclass
class AppContext:
    browsers: dict[str, SimpleBrowserTool] = field(default_factory=dict)

    def create_or_get_browser(self, session_id: str) -> SimpleBrowserTool:
        if session_id not in self.browsers:
            backend = ExaBackend(source="web")
            self.browsers[session_id] = SimpleBrowserTool(backend=backend)
        return self.browsers[session_id]

    def remove_browser(self, session_id: str) -> None:
        self.browsers.pop(session_id, None)


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    yield AppContext()


# Pass lifespan to server
mcp = FastMCP(
    name="browser",
    instructions=r"""
Tool for browsing.
The `cursor` appears in brackets before each browsing display: `[{cursor}]`.
Cite information from the tool using the following format:
`【{cursor}†L{line_start}(-L{line_end})?】`, for example: `【6†L9-L11】` or `【8†L3】`. 
Do not quote more than 10 words directly from the tool output.
sources=web
""".strip(),
    lifespan=app_lifespan,
    port=8001,
)


@mcp.tool(
    name="search",
    title="Search for information",
    description=
    "Searches for information related to `query` and displays `topn` results.",
)
async def search(ctx: Context,
                 query: str,
                 topn: int = 10,
                 source: Optional[str] = None) -> str:
    """Search for information related to a query"""
    browser = ctx.request_context.lifespan_context.create_or_get_browser(
        ctx.client_id)
    messages = []
    async for message in browser.search(query=query, topn=topn, source=source):
        if message.content and hasattr(message.content[0], 'text'):
            messages.append(message.content[0].text)
    return "\n".join(messages)


@mcp.tool(
    name="open",
    title="Open a link or page",
    description="""
Opens the link `id` from the page indicated by `cursor` starting at line number `loc`, showing `num_lines` lines.
Valid link ids are displayed with the formatting: `【{id}†.*】`.
If `cursor` is not provided, the most recent page is implied.
If `id` is a string, it is treated as a fully qualified URL associated with `source`.
If `loc` is not provided, the viewport will be positioned at the beginning of the document or centered on the most relevant passage, if available.
Use this function without `id` to scroll to a new location of an opened page.
""".strip(),
)
async def open_link(ctx: Context,
                    id: Union[int, str] = -1,
                    cursor: int = -1,
                    loc: int = -1,
                    num_lines: int = -1,
                    view_source: bool = False,
                    source: Optional[str] = None) -> str:
    """Open a link or navigate to a page location"""
    browser = ctx.request_context.lifespan_context.create_or_get_browser(
        ctx.client_id)
    messages = []
    async for message in browser.open(id=id,
                                      cursor=cursor,
                                      loc=loc,
                                      num_lines=num_lines,
                                      view_source=view_source,
                                      source=source):
        if message.content and hasattr(message.content[0], 'text'):
            messages.append(message.content[0].text)
    return "\n".join(messages)


@mcp.tool(
    name="find",
    title="Find pattern in page",
    description=
    "Finds exact matches of `pattern` in the current page, or the page given by `cursor`.",
)
async def find_pattern(ctx: Context, pattern: str, cursor: int = -1) -> str:
    """Find exact matches of a pattern in the current page"""
    browser = ctx.request_context.lifespan_context.create_or_get_browser(
        ctx.client_id)
    messages = []
    async for message in browser.find(pattern=pattern, cursor=cursor):
        if message.content and hasattr(message.content[0], 'text'):
            messages.append(message.content[0].text)
    return "\n".join(messages)


if __name__ == "__main__":
    import uvicorn
    # Get the ASGI application from the FastMCP instance
    app = mcp.http_app
    uvicorn.run(app, host="0.0.0.0", port=8001)