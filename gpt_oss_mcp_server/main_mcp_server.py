from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Union, Optional, AsyncIterator

from mcp.server.fastmcp import Context, FastMCP
from gpt_oss_mcp_server.browser_server import SimpleBrowserTool
from gpt_oss_mcp_server.browser_server import ExaBackend
from gpt_oss_mcp_server.python_server import PythonTool
from openai_harmony import Message, TextContent, Author, Role
from gpt_oss_mcp_server.orchestrator_service import SessionInfo


@dataclass
class AppContext:
    browsers: dict[str, SimpleBrowserTool] = field(default_factory=dict)
    user_sessions: dict[str, dict[str, SessionInfo]] = field(default_factory=dict)

    def create_or_get_browser(self, session_id: str) -> SimpleBrowserTool:
        if session_id not in self.browsers:
            backend = ExaBackend(source="web")
            self.browsers[session_id] = SimpleBrowserTool(backend=backend)
        return self.browsers[session_id]

    def remove_browser(self, session_id: str) -> None:
        self.browsers.pop(session_id, None)

    def get_user_session(self, user_id: str, session_id: str) -> Optional[SessionInfo]:
        return self.user_sessions.get(user_id, {}).get(session_id)

    def create_user_session(self, user_id: str, session_id: str, initial_data: Optional[Dict[str, Any]] = None) -> SessionInfo:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        session_info = SessionInfo(session_id=session_id, user_id=user_id, session_data=initial_data or {})
        self.user_sessions[user_id][session_id] = session_info
        return session_info

    def update_user_session(self, user_id: str, session_id: str, new_session_data: Optional[Dict[str, Any]] = None):
        if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
            if new_session_data is not None:
                self.user_sessions[user_id][session_id].session_data.update(new_session_data)

    def close_user_session(self, user_id: str, session_id: str):
        if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
            del self.user_sessions[user_id][session_id]
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    yield AppContext()


mcp = FastMCP(
    name="orchestrator",
    instructions="""
    This is the central orchestrator for the AI Operating System. It routes commands to various MCP servers.
    """.strip(),
    lifespan=app_lifespan,
    port=9000,
)


# Python Server Integration
@mcp.tool(
    name="python",
    title="Execute Python code",
    description="""
Use this tool to execute Python code in your chain of thought. The code will not be shown to the user. This tool should be used for internal reasoning, but not for code that is intended to be visible to the user (e.g. when creating plots, tables, or files).
When you send a message containing python code to python, it will be executed in a stateless docker container, and the stdout of that process will be returned to you.
    """.strip(),
    annotations={
        "include_in_prompt": False,
    })
async def python(code: str) -> str:
    tool = PythonTool()
    messages = []
    async for message in tool.process(
            Message(author=Author(role=Role.TOOL, name="python"),
                    content=[TextContent(text=code)])):
        messages.append(message)
    return "\n".join([message.content[0].text for message in messages])


# Browser Server Integration
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


# The FastMCP instance itself is the ASGI application
app = mcp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True)