import uvicorn
from fastapi import FastAPI
from mcp.server import FastMCP
from servers.system_operations_server.app_launcher import AppLauncher
from servers.system_operations_server.file_ops import FileOperations
from shared.error_handling import configure_error_handling

app = FastAPI()

# Configure error handling
configure_error_handling(app)

mcp = FastMCP()
app_launcher = AppLauncher()
file_ops = FileOperations()

from typing import Dict, Any

@mcp.tool(
    name="launch_app"
)
async def launch_app(app_name: str) -> Dict[str, Any]:
    return app_launcher.launch_app(app_name)

@mcp.tool(
    name="read_file"
)
async def read_file(file_path: str) -> str:
    return file_ops.read_file(file_path)

@mcp.tool(
    name="write_file"
)
async def write_file(file_path: str, content: str) -> bool:
    return file_ops.write_file(file_path, content)

@mcp.tool(
    name="delete_file"
)
async def delete_file(file_path: str) -> bool:
    return file_ops.delete_file(file_path)

app.mount("/mcp", mcp)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)