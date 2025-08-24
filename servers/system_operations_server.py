#!/usr/bin/env python3
"""
System Operations Server (Port 8002)
Provides system-level operations for the GPT-OSS AI OS
"""

import asyncio
import psutil
import subprocess
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="System Operations Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SystemCommand(BaseModel):
    command: str
    args: List[str] = []
    timeout: int = 30

class FileOperation(BaseModel):
    path: str
    operation: str  # read, write, delete, create
    content: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    uptime: float
    memory_usage: Dict[str, Any]
    cpu_usage: float
    disk_usage: Dict[str, Any]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for system operations server"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            uptime=psutil.boot_time(),
            memory_usage={
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            cpu_usage=cpu_percent,
            disk_usage={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- System Resource Monitoring ---

class ResourceLimits(BaseModel):
    cpu_threshold: Optional[float] = None
    memory_threshold: Optional[float] = None
    disk_threshold: Optional[float] = None

# In-memory storage for resource limits
resource_limits: Dict[str, ResourceLimits] = {}

@app.post("/system/set_resource_limits")
async def set_resource_limits(limits: ResourceLimits):
    """Set thresholds for CPU, memory, and disk usage."""
    try:
        if limits.cpu_threshold is not None:
            resource_limits["cpu"] = limits.cpu_threshold
        if limits.memory_threshold is not None:
            resource_limits["memory"] = limits.memory_threshold
        if limits.disk_threshold is not None:
            resource_limits["disk"] = limits.disk_threshold
        logger.info(f"Resource limits updated: {resource_limits}")
        return {"message": "Resource limits set successfully", "current_limits": resource_limits}
    except Exception as e:
        logger.error(f"Failed to set resource limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SystemResources(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, Any]
    network_io: Dict[str, Any]

@app.get("/system/resources", response_model=SystemResources)
async def get_system_resources():
    """Retrieves current system resource usage (CPU, memory, disk, network)."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent

        disk_usage = {disk.mountpoint: psutil.disk_usage(disk.mountpoint)._asdict() 
                      for disk in psutil.disk_partitions()}
        
        network_io = psutil.net_io_counters(pernic=True)

        return SystemResources(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage=disk_usage,
            network_io=network_io
        )
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/info")
async def get_system_info():
    """Get comprehensive system information"""
    try:
        info = {
            "cpu": {
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": psutil.virtual_memory()._asdict(),
            "disk": {
                "partitions": [],
                "usage": {}
            },
            "network": {},
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        # Get disk partitions
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info["disk"]["partitions"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                })
            except PermissionError:
                continue
        
        # Get network interfaces
        interfaces = psutil.net_if_addrs()
        for interface_name, interface_addresses in interfaces.items():
            info["network"][interface_name] = [
                {
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                    "ptp": addr.ptp
                }
                for addr in interface_addresses
            ]
        
        return info
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/monitor_resources")
async def monitor_resources():
    """Continuously monitors system resources against set thresholds."""
    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_usage = psutil.disk_usage('/')

            if "cpu" in resource_limits and cpu_percent > resource_limits["cpu"]:
                logger.warning(f"CPU usage ({cpu_percent}%) exceeds threshold ({resource_limits['cpu']}%)")
            if "memory" in resource_limits and memory_info.percent > resource_limits["memory"]:
                logger.warning(f"Memory usage ({memory_info.percent}%) exceeds threshold ({resource_limits['memory']}%)")
            if "disk" in resource_limits and disk_usage.percent > resource_limits["disk"]:
                logger.warning(f"Disk usage ({disk_usage.percent}%) exceeds threshold ({resource_limits['disk']}%)")

            await asyncio.sleep(5) # Check every 5 seconds
        except Exception as e:
            logger.error(f"Error during resource monitoring: {e}")
            break # Exit loop on error

@app.post("/system/execute")
async def execute_system_command(command: SystemCommand):
    """Execute system commands with safety checks"""
    try:
        # Security: whitelist allowed commands
        allowed_commands = {
            'ls', 'pwd', 'cat', 'grep', 'find', 'df', 'du', 'ps', 'top', 'whoami',
            'mkdir', 'touch', 'cp', 'mv', 'rm', 'chmod', 'chown', 'kill', 'pkill'
        }
        
        if command.command not in allowed_commands:
            raise HTTPException(
                status_code=400, 
                detail=f"Command '{command.command}' not allowed"
            )
        
        cmd = [command.command] + command.args
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=command.timeout
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/file/operation")
async def file_operation(operation: FileOperation):
    """Perform file operations with safety checks"""
    try:
        # Security: validate path
        base_path = os.path.abspath(os.getcwd())
        target_path = os.path.abspath(operation.path)
        
        if not target_path.startswith(base_path):
            raise HTTPException(status_code=400, detail="Path traversal detected")
        
        if operation.operation == "read":
            if not os.path.exists(target_path):
                raise HTTPException(status_code=404, detail="File not found")
            if not os.path.isfile(target_path):
                raise HTTPException(status_code=400, detail="Path is not a file")
            if not os.access(target_path, os.R_OK):
                raise HTTPException(status_code=403, detail="Permission denied: Cannot read file")
            with open(target_path, 'r') as f:
                content = f.read()
            return {"content": content, "path": target_path}
        
        elif operation.operation == "write":
            if os.path.exists(target_path) and not os.path.isfile(target_path):
                raise HTTPException(status_code=400, detail="Path exists and is not a file")
            if os.path.exists(target_path) and not os.access(target_path, os.W_OK):
                raise HTTPException(status_code=403, detail="Permission denied: Cannot write to file")
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w') as f:
                f.write(operation.content or "")
            return {"message": "File written successfully", "path": target_path}
        
        elif operation.operation == "delete":
            if not os.path.exists(target_path):
                raise HTTPException(status_code=404, detail="File not found")
            if not os.path.isfile(target_path):
                raise HTTPException(status_code=400, detail="Path is not a file")
            if not os.access(target_path, os.W_OK):
                raise HTTPException(status_code=403, detail="Permission denied: Cannot delete file")
            os.remove(target_path)
            return {"message": "File deleted successfully", "path": target_path}

        elif operation.operation == "create":
            if os.path.exists(target_path):
                raise HTTPException(status_code=400, detail="File already exists")
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w') as f:
                f.write(operation.content or "")
            return {"message": "File created successfully", "path": target_path}

        else:
            raise HTTPException(status_code=400, detail="Invalid file operation")

    except Exception as e:
        logger.error(f"File operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Hardware Interaction Module (USB/Bluetooth) ---

@app.get("/hardware/usb/list")
async def list_usb_devices():
    """Lists connected USB devices."""
    try:
        # This is a placeholder. Actual implementation would require a library like pyusb or platform-specific commands.
        # Example using a system command (lsusb on Linux, system_profiler SPUSBDataType on macOS)
        if os.name == 'posix': # Linux or macOS
            if os.uname().sysname == 'Darwin': # macOS
                cmd = ["system_profiler", "SPUSBDataType"]
            else: # Linux
                cmd = ["lsusb"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {"devices": stdout.decode().strip().split('\n')}
            else:
                logger.error(f"Failed to list USB devices: {stderr.decode()}")
                raise HTTPException(status_code=500, detail=f"Failed to list USB devices: {stderr.decode()}")
        else:
            raise HTTPException(status_code=501, detail="USB device listing not supported on this OS")
    except Exception as e:
        logger.error(f"Error listing USB devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hardware/bluetooth/list")
async def list_bluetooth_devices():
    """Lists paired or discovered Bluetooth devices."""
    try:
        # This is a placeholder. Actual implementation would require a library like PyBluez or platform-specific commands.
        # Example using a system command (bluetoothctl on Linux, system_profiler SPBluetoothDataType on macOS)
        if os.name == 'posix': # Linux or macOS
            if os.uname().sysname == 'Darwin': # macOS
                cmd = ["system_profiler", "SPBluetoothDataType"]
            else: # Linux
                cmd = ["bluetoothctl", "devices"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {"devices": stdout.decode().strip().split('\n')}
            else:
                logger.error(f"Failed to list Bluetooth devices: {stderr.decode()}")
                raise HTTPException(status_code=500, detail=f"Failed to list Bluetooth devices: {stderr.decode()}")
        else:
            raise HTTPException(status_code=501, detail="Bluetooth device listing not supported on this OS")
    except Exception as e:
        logger.error(f"Error listing Bluetooth devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Application Launching and Process Monitoring ---

class ApplicationLaunch(BaseModel):
    path: str
    args: List[str] = []
    name: Optional[str] = None # Optional name for the process

class ProcessInfo(BaseModel):
    pid: int
    name: str
    status: str
    create_time: datetime
    cpu_percent: float
    memory_percent: float
    cmdline: List[str]

active_processes: Dict[int, subprocess.Popen] = {}

@app.post("/applications/launch", response_model=ProcessInfo)
async def launch_application(app_launch: ApplicationLaunch):
    """Launches an application and returns its process information."""
    try:
        # Security: Basic path validation
        if not os.path.isabs(app_launch.path):
            raise HTTPException(status_code=400, detail="Application path must be absolute")
        if not os.path.exists(app_launch.path):
            raise HTTPException(status_code=404, detail="Application not found")
        if not os.path.isfile(app_launch.path) and not os.access(app_launch.path, os.X_OK):
            raise HTTPException(status_code=400, detail="Path is not an executable file")

        process = subprocess.Popen([app_launch.path] + app_launch.args, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
        active_processes[process.pid] = process
        logger.info(f"Launched application {app_launch.name or app_launch.path} with PID {process.pid}")
        
        p = psutil.Process(process.pid)
        return ProcessInfo(
            pid=p.pid,
            name=p.name(),
            status=p.status(),
            create_time=datetime.fromtimestamp(p.create_time()),
            cpu_percent=p.cpu_percent(interval=0.1),
            memory_percent=p.memory_percent(),
            cmdline=p.cmdline()
        )
    except Exception as e:
        logger.error(f"Error launching application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/applications/processes", response_model=List[ProcessInfo])
async def list_processes():
    """Lists all currently active processes launched by this server."""
    processes_info = []
    for pid, proc in list(active_processes.items()): # Use list to allow modification during iteration
        if proc.poll() is not None: # Process has terminated
            del active_processes[pid]
            continue
        try:
            p = psutil.Process(pid)
            processes_info.append(ProcessInfo(
                pid=p.pid,
                name=p.name(),
                status=p.status(),
                create_time=datetime.fromtimestamp(p.create_time()),
                cpu_percent=p.cpu_percent(interval=0.1),
                memory_percent=p.memory_percent(),
                cmdline=p.cmdline()
            ))
        except psutil.NoSuchProcess:
            del active_processes[pid]
            continue
        except Exception as e:
            logger.warning(f"Could not get info for PID {pid}: {e}")
            continue
    return processes_info

@app.post("/applications/terminate")
async def terminate_application(pid: int):
    """Terminates a launched application by its PID."""
    if pid not in active_processes:
        raise HTTPException(status_code=404, detail="Process not found or not launched by this server")
    
    try:
        process = active_processes[pid]
        process.terminate() # or process.kill()
        process.wait(timeout=5) # Wait for process to terminate
        del active_processes[pid]
        logger.info(f"Terminated process with PID {pid}")
        return {"message": f"Process {pid} terminated successfully"}
    except psutil.NoSuchProcess:
        del active_processes[pid] # Clean up if process already gone
        raise HTTPException(status_code=404, detail="Process not found")
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        del active_processes[pid]
        logger.warning(f"Process {pid} did not terminate gracefully, killed it.")
        return {"message": f"Process {pid} terminated forcefully after timeout"}
    except Exception as e:
        logger.error(f"Error terminating process {pid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/hardware/devices")
async def get_connected_devices():
    """Get information about connected hardware devices (USB, Bluetooth)."""
    try:
        devices = {
            "usb_devices": [],
            "bluetooth_devices": []
        }

        # psutil does not directly provide USB/Bluetooth device listing.
        # This would typically require platform-specific libraries or parsing system command outputs.
        # For demonstration, we'll return a placeholder or integrate a simple check if available.
        # Example (conceptual, requires external library like pyudev for Linux or wmi for Windows):
        # if platform.system() == "Linux":
        #     import pyudev
        #     context = pyudev.Context()
        #     for device in context.list_devices(subsystem='usb'):
        #         devices["usb_devices"].append({"vendor_id": device.get('ID_VENDOR_ID'), "model_id": device.get('ID_MODEL_ID'), "vendor": device.get('ID_VENDOR'), "model": device.get('ID_MODEL')})

        # For now, returning a placeholder or basic system info that might hint at devices
        return devices
    except Exception as e:
        logger.error(f"Failed to get connected devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/file/operation")
async def file_operation(operation: FileOperationRequest):
    """Perform file operations (read, write, delete, create)."""
    file_path = os.path.abspath(operation.path)

    # Basic path validation to prevent directory traversal
    if not file_path.startswith(os.getcwd()):
        raise HTTPException(status_code=400, detail="Access denied: Path outside working directory.")

    try:
        if operation.type == "read":
            if not os.path.isfile(file_path):
                raise HTTPException(status_code=404, detail="File not found.")
            with open(file_path, "r") as f:
                content = f.read()
            return {"status": "success", "content": content}
        elif operation.type == "write":
            # Ensure directory exists for the file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(operation.content or "")
            return {"status": "success", "message": "File written successfully."}
        elif operation.type == "delete":
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path) # DANGER: This will delete directories recursively
                return {"status": "success", "message": "File/Directory deleted successfully."}
            else:
                raise HTTPException(status_code=404, detail="File/Directory not found.")
        elif operation.type == "create":
            if os.path.exists(file_path):
                raise HTTPException(status_code=409, detail="File/Directory already exists.")
            if operation.is_directory:
                os.makedirs(file_path)
            else:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(operation.content or "")
            return {"status": "success", "message": "File/Directory created successfully."}
        else:
            raise HTTPException(status_code=400, detail="Invalid operation type.")
    except Exception as e:
        logger.error(f"File operation failed for {operation.path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/processes", response_model=List[Dict[str, Any]])
async def get_process_list():
    """Get a list of all running processes."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            processes.append(proc.info)
        return processes
    except Exception as e:
        logger.error(f"Failed to get process list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/kill_process")
async def kill_process(pid: int):
    """Kill a process by PID."""
    try:
        p = psutil.Process(pid)
        p.terminate()  # or p.kill()
        return {"message": f"Process {pid} terminated successfully"}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process with PID {pid} not found")
    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/environment")
async def get_environment_variables():
    """Get all environment variables."""
    return dict(os.environ)

@app.get("/system/list_directory")
async def list_directory(path: str = "."):
    """List contents of a directory."""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.isdir(abs_path):
            raise HTTPException(status_code=404, detail="Directory not found")
        
        items = []
        for item in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item)
            items.append({
                "name": item,
                "is_dir": os.path.isdir(item_path),
                "is_file": os.path.isfile(item_path),
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                "last_modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        return items
    except Exception as e:
        logger.error(f"Failed to list directory {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/processes", response_model=List[Dict[str, Any]])
async def get_process_list():
    """Get a list of all running processes."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            processes.append(proc.info)
        return processes
    except Exception as e:
        logger.error(f"Failed to get process list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/kill_process")
async def kill_process(pid: int):
    """Kill a process by PID."""
    try:
        p = psutil.Process(pid)
        p.terminate()  # or p.kill()
        return {"message": f"Process {pid} terminated successfully"}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process with PID {pid} not found")
    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/list_directory")
async def list_directory(path: str = "."):
    """List contents of a directory."""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.isdir(abs_path):
            raise HTTPException(status_code=404, detail="Directory not found")
        
        items = []
        for item in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item)
            items.append({
                "name": item,
                "is_dir": os.path.isdir(item_path),
                "is_file": os.path.isfile(item_path),
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                "last_modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        return items
    except Exception as e:
        logger.error(f"Failed to list directory {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)