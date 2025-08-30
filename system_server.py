from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel
import psutil
import platform
import socket
import time
from typing import List, Dict, Optional

app = FastAPI()
mcp = FastMCP(name="system")
app.mount("/mcp", mcp)

class SystemInfo(BaseModel):
    hostname: str
    platform: str
    cpu_count: int
    cpu_percent: float
    memory_total: int
    memory_available: int
    memory_used: int
    memory_percent: float
    boot_time: float
    uptime: float

class ProcessInfo(BaseModel):
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: float

class DiskUsage(BaseModel):
    total: int
    used: int
    free: int
    percent: float

class NetworkInfo(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int

@mcp.tool()
async def get_system_info() -> SystemInfo:
    """Get comprehensive system information including CPU, memory, and uptime."""
    memory = psutil.virtual_memory()
    return SystemInfo(
        hostname=socket.gethostname(),
        platform=f"{platform.system()} {platform.release()}",
        cpu_count=psutil.cpu_count(),
        cpu_percent=psutil.cpu_percent(),
        memory_total=memory.total,
        memory_available=memory.available,
        memory_used=memory.used,
        memory_percent=memory.percent,
        boot_time=psutil.boot_time(),
        uptime=time.time() - psutil.boot_time()
    )

@mcp.tool()
async def get_processes() -> List[ProcessInfo]:
    """Get list of running processes with their resource usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time']):
        try:
            processes.append(ProcessInfo(
                pid=proc.info['pid'],
                name=proc.info['name'],
                status=proc.info['status'],
                cpu_percent=proc.info['cpu_percent'],
                memory_percent=proc.info['memory_percent'],
                create_time=proc.info['create_time']
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return processes

@mcp.tool()
async def get_disk_usage(path: str = '/') -> DiskUsage:
    """Get disk usage information for the specified path."""
    usage = psutil.disk_usage(path)
    return DiskUsage(
        total=usage.total,
        used=usage.used,
        free=usage.free,
        percent=usage.percent
    )

@mcp.tool()
async def get_network_info() -> NetworkInfo:
    """Get network usage statistics."""
    counters = psutil.net_io_counters()
    return NetworkInfo(
        bytes_sent=counters.bytes_sent,
        bytes_recv=counters.bytes_recv,
        packets_sent=counters.packets_sent,
        packets_recv=counters.packets_recv
    )

@mcp.tool()
async def restart_service(service_name: str) -> bool:
    """Attempt to restart a system service."""
    try:
        # This would require appropriate permissions
        # Implementation depends on the OS
        return True
    except Exception:
        return False

@mcp.tool()
async def shutdown_system(delay: int = 0) -> bool:
    """Schedule system shutdown after specified delay in seconds."""
    # This would require appropriate permissions
    # Implementation depends on the OS
    return False

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)