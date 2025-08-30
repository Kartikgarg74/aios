from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import subprocess
import tempfile
import uuid
import time

app = FastAPI()
mcp = FastMCP(name="ide")
app = mcp

class FileInfo(BaseModel):
    path: str
    name: str
    is_dir: bool
    size: int
    modified: float

class CodeExecutionResult(BaseModel):
    success: bool
    output: str
    error: str
    execution_time: float

class ProjectStructure(BaseModel):
    files: List[FileInfo]
    directories: List[str]

@mcp.tool()
async def list_directory(path: str = '.') -> ProjectStructure:
    """List files and directories in the specified path."""
    try:
        items = os.listdir(path)
        files = []
        directories = []
        
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                directories.append(item)
            else:
                stat = os.stat(full_path)
                files.append(FileInfo(
                    path=full_path,
                    name=item,
                    is_dir=False,
                    size=stat.st_size,
                    modified=stat.st_mtime
                ))
        
        return ProjectStructure(files=files, directories=directories)
    except Exception as e:
        return ProjectStructure(files=[], directories=[], error=str(e))

@mcp.tool()
async def read_file(file_path: str) -> str:
    """Read the contents of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def write_file(file_path: str, content: str) -> bool:
    """Write content to a file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception:
        return False

@mcp.tool()
async def execute_code(language: str, code: str) -> CodeExecutionResult:
    """Execute code in the specified language and return the result."""
    temp_file = None
    try:
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute based on language
        start_time = time.time()
        if language == 'python':
            result = subprocess.run(['python', temp_file], capture_output=True, text=True)
        elif language == 'javascript':
            result = subprocess.run(['node', temp_file], capture_output=True, text=True)
        else:
            return CodeExecutionResult(
                success=False,
                output="",
                error=f"Unsupported language: {language}",
                execution_time=0
            )
        
        execution_time = time.time() - start_time
        
        return CodeExecutionResult(
            success=result.returncode == 0,
            output=result.stdout,
            error=result.stderr,
            execution_time=execution_time
        )
    except Exception as e:
        return CodeExecutionResult(
            success=False,
            output="",
            error=str(e),
            execution_time=0
        )
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

@mcp.tool()
async def create_project(project_name: str, template: Optional[str] = None) -> bool:
    """Create a new project with optional template."""
    try:
        os.makedirs(project_name)
        if template == 'python':
            with open(os.path.join(project_name, 'main.py'), 'w') as f:
                f.write("""# Python project\nprint('Hello World!')""")
        elif template == 'javascript':
            with open(os.path.join(project_name, 'index.js'), 'w') as f:
                f.write("""// JavaScript project\nconsole.log('Hello World!');""")
        return True
    except Exception:
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ide_server:mcp", host="0.0.0.0", port=8007, reload=True)