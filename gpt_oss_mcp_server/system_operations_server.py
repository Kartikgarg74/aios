"""
System Operations Server for AI Operating System
Port: 8002
Handles file system operations, application launching, process management,
and system information gathering.
"""

import asyncio
import os
import subprocess
import platform
import psutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import Context, FastMCP


@dataclass
class SystemInfo:
    """System information container"""
    platform: str
    architecture: str
    hostname: str
    cpu_count: int
    memory_total: int
    disk_usage: Dict[str, Any]
    network_interfaces: List[str]


@dataclass
class ProcessInfo:
    """Process information container"""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_mb: float
    cmdline: List[str]


@dataclass
class AppContext:
    """Application context for system operations"""
    active_processes: Dict[int, ProcessInfo] = field(default_factory=dict)
    launched_apps: Dict[str, subprocess.Popen] = field(default_factory=dict)


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle"""
    context = AppContext()
    try:
        yield context
    finally:
        # Cleanup launched applications
        for app_name, process in context.launched_apps.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass


# Create the FastMCP server
mcp = FastMCP(
    name="system_operations",
    instructions="""
    System Operations Server for AI Operating System.
    
    This server provides comprehensive system management capabilities including:
    - File system operations (create, read, update, delete files and directories)
    - Application launching and management
    - Process monitoring and control
    - System information gathering
    - Hardware interaction and monitoring
    
    All operations are sandboxed and require appropriate permissions.
    """.strip(),
    lifespan=app_lifespan,
    port=8002,
)


@mcp.tool(
    name="get_system_info",
    title="Get System Information",
    description="Retrieves comprehensive system information including platform, hardware specs, and current state"
)
async def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    try:
        # Basic system info
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used,
                "free": psutil.virtual_memory().free
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "boot_time": psutil.boot_time(),
            "network_interfaces": list(psutil.net_io_counters(pernic=True).keys())
        }
        
        return system_info
    except Exception as e:
        return {"error": f"Failed to get system info: {str(e)}"}


@mcp.tool(
    name="list_files",
    title="List Files and Directories",
    description="Lists files and directories in a given path with detailed information"
)
async def list_files(path: str = ".", recursive: bool = False) -> Dict[str, Any]:
    """List files and directories in a given path"""
    try:
        target_path = Path(path).expanduser().resolve()
        
        if not target_path.exists():
            return {"error": f"Path does not exist: {path}"}
        
        files_info = []
        
        if recursive:
            for item in target_path.rglob("*"):
                stat = item.stat()
                files_info.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                    "is_hidden": item.name.startswith(".")
                })
        else:
            for item in target_path.iterdir():
                stat = item.stat()
                files_info.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                    "is_hidden": item.name.startswith(".")
                })
        
        return {
            "directory": str(target_path),
            "files": files_info,
            "total_count": len(files_info)
        }
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}"}


@mcp.tool(
    name="create_file",
    title="Create or Update File",
    description="Creates a new file or updates an existing one with the provided content"
)
async def create_file(filepath: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
    """Create or update a file with content"""
    try:
        target_path = Path(filepath).expanduser().resolve()
        
        if create_dirs:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        stat = target_path.stat()
        return {
            "success": True,
            "file": str(target_path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime
        }
    except Exception as e:
        return {"error": f"Failed to create file: {str(e)}"}


@mcp.tool(
    name="read_file",
    title="Read File Content",
    description="Reads the content of a file and returns it as text"
)
async def read_file(filepath: str, max_size: int = 1024*1024) -> Dict[str, Any]:
    """Read file content"""
    try:
        target_path = Path(filepath).expanduser().resolve()
        
        if not target_path.exists():
            return {"error": f"File does not exist: {filepath}"}
        
        if not target_path.is_file():
            return {"error": f"Path is not a file: {filepath}"}
        
        if target_path.stat().st_size > max_size:
            return {"error": f"File too large: {target_path.stat().st_size} bytes"}
        
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            "content": content,
            "file": str(target_path),
            "size": len(content),
            "lines": content.count('\n') + 1
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


@mcp.tool(
    name="delete_file",
    title="Delete File or Directory",
    description="Deletes a file or directory (recursively for directories)"
)
async def delete_file(filepath: str, force: bool = False) -> Dict[str, Any]:
    """Delete file or directory"""
    try:
        target_path = Path(filepath).expanduser().resolve()
        
        if not target_path.exists():
            return {"error": f"Path does not exist: {filepath}"}
        
        if target_path.is_dir():
            if not force:
                return {"error": "Use force=True to delete directories"}
            import shutil
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
        
        return {"success": True, "deleted": str(target_path)}
    except Exception as e:
        return {"error": f"Failed to delete: {str(e)}"}


@mcp.tool(
    name="launch_application",
    title="Launch Application",
    description="Launches an application by name or path with optional arguments"
)
async def launch_application(app_name: str, args: List[str] = None, wait: bool = False) -> Dict[str, Any]:
    """Launch an application"""
    try:
        args = args or []
        system = platform.system()
        
        # Platform-specific application launching
        if system == "Darwin":  # macOS
            # Try common macOS applications
            app_paths = [
                f"/Applications/{app_name}.app",
                f"/System/Applications/{app_name}.app",
                f"/System/Applications/Utilities/{app_name}.app"
            ]
            
            for app_path in app_paths:
                if Path(app_path).exists():
                    cmd = ["open", "-a", app_path] + args
                    break
            else:
                # Try direct command
                cmd = [app_name] + args
                
        elif system == "Windows":
            # Windows applications
            cmd = ["start", app_name] + args
            
        elif system == "Linux":
            # Linux applications
            cmd = [app_name] + args
            
        else:
            return {"error": f"Unsupported platform: {system}"}
        
        # Launch the application
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if wait:
            stdout, stderr = process.communicate()
            return {
                "success": True,
                "app": app_name,
                "pid": process.pid,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
        else:
            return {
                "success": True,
                "app": app_name,
                "pid": process.pid,
                "launched": True
            }
            
    except Exception as e:
        return {"error": f"Failed to launch application: {str(e)}"}


@mcp.tool(
    name="list_processes",
    title="List Running Processes",
    description="Lists all running processes with detailed information"
)
async def list_processes(sort_by: str = "cpu") -> List[Dict[str, Any]]:
    """List running processes"""
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'cmdline']):
            try:
                pinfo = proc.info
                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "status": pinfo['status'],
                    "cpu_percent": pinfo['cpu_percent'],
                    "memory_mb": proc.memory_info().rss / (1024 * 1024),
                    "cmdline": pinfo['cmdline'] or []
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort processes
        if sort_by == "cpu":
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == "memory":
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        elif sort_by == "name":
            processes.sort(key=lambda x: x['name'])
        
        return processes[:50]  # Return top 50 processes
    except Exception as e:
        return [{"error": f"Failed to list processes: {str(e)}"}]


@mcp.tool(
    name="kill_process",
    title="Kill Process",
    description="Kills a process by PID or name"
)
async def kill_process(pid: Optional[int] = None, name: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Kill a process by PID or name"""
    try:
        if pid:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            
            return {"success": True, "killed": pid, "name": proc.name()}
            
        elif name:
            killed = []
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and name.lower() in proc.info['name'].lower():
                    try:
                        if force:
                            proc.kill()
                        else:
                            proc.terminate()
                        killed.append(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            return {"success": True, "killed": killed, "name": name}
            
        else:
            return {"error": "Must provide either pid or name"}
            
    except psutil.NoSuchProcess:
        return {"error": "Process not found"}
    except Exception as e:
        return {"error": f"Failed to kill process: {str(e)}"}


@mcp.tool(
    name="create_directory",
    title="Create Directory",
    description="Creates a directory structure (including parent directories if needed)"
)
async def create_directory(path: str, exist_ok: bool = True) -> Dict[str, Any]:
    """Create directory structure"""
    try:
        target_path = Path(path).expanduser().resolve()
        target_path.mkdir(parents=True, exist_ok=exist_ok)
        
        return {
            "success": True,
            "directory": str(target_path),
            "created": True,
            "exists": target_path.exists()
        }
    except Exception as e:
        return {"error": f"Failed to create directory: {str(e)}"}


@mcp.tool(
    name="get_directory_size",
    title="Get Directory Size",
    description="Calculates the total size of a directory and its contents"
)
async def get_directory_size(path: str) -> Dict[str, Any]:
    """Get directory size information"""
    try:
        target_path = Path(path).expanduser().resolve()
        
        if not target_path.exists():
            return {"error": f"Path does not exist: {path}"}
        
        total_size = 0
        file_count = 0
        
        if target_path.is_file():
            total_size = target_path.stat().st_size
            file_count = 1
        else:
            for file_path in target_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return {
            "path": str(target_path),
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
            "file_count": file_count
        }
    except Exception as e:
        return {"error": f"Failed to get directory size: {str(e)}"}


# The FastMCP instance itself is the ASGI application
app = mcp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gpt_oss_mcp_server.system_operations_server:app", host="0.0.0.0", port=8002, reload=True)