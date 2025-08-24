"""
IDE Integration Server for AI Operating System
Port: 8004
Handles VS Code control, file editing, git operations, code analysis,
and direct IDE integration capabilities.
"""

import asyncio
import json
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import datetime

from mcp.server.fastmcp import Context, FastMCP


@dataclass
class WorkspaceInfo:
    """Workspace information container"""
    root_path: str
    folders: List[str]
    files: List[str]
    git_branch: Optional[str] = None
    git_status: Optional[str] = None


@dataclass
class GitInfo:
    """Git repository information"""
    branch: str
    status: str
    commits_ahead: int = 0
    commits_behind: int = 0
    modified_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    staged_files: List[str] = field(default_factory=list)


@dataclass
class CodeAnalysis:
    """Code analysis results"""
    file_path: str
    language: str
    lines_of_code: int
    complexity_score: int
    issues: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    imports: List[str]


@dataclass
class AppContext:
    """Application context for IDE operations"""
    active_workspaces: Dict[str, WorkspaceInfo] = field(default_factory=dict)
    recent_files: List[str] = field(default_factory=list)
    
    def get_workspace(self, session_id: str, workspace_path: str = None) -> WorkspaceInfo:
        if workspace_path:
            self.active_workspaces[session_id] = WorkspaceInfo(
                root_path=workspace_path,
                folders=[],
                files=[]
            )
        return self.active_workspaces.get(session_id, WorkspaceInfo(
            root_path=str(Path.cwd()),
            folders=[],
            files=[]
        ))


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle"""
    context = AppContext()
    try:
        yield context
    finally:
        # Cleanup workspaces
        context.active_workspaces.clear()


# Create the FastMCP server
mcp = FastMCP(
    name="ide_integration",
    instructions="""
    IDE Integration Server for AI Operating System.
    
    This server provides comprehensive IDE control including:
    - VS Code workspace management
    - File editing and navigation
    - Git operations (commit, push, pull, branch management)
    - Code analysis and linting
    - Extension management
    - Build and test execution
    - Debugging assistance
    
    All operations are performed in the context of the current workspace.
    """.strip(),
    lifespan=app_lifespan,
    port=8004,
)


@mcp.tool(
    name="open_workspace",
    title="Open VS Code Workspace",
    description="Opens a VS Code workspace at the specified directory"
)
async def open_workspace(ctx: Context, workspace_path: str, new_window: bool = False) -> Dict[str, Any]:
    """Open VS Code workspace"""
    try:
        workspace_path = Path(workspace_path).expanduser().resolve()
        
        if not workspace_path.exists():
            return {"error": f"Workspace path does not exist: {workspace_path}"}
        
        # Open VS Code
        cmd = ["code"]
        if new_window:
            cmd.append("--new-window")
        cmd.append(str(workspace_path))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get workspace info
            folders = [str(d) for d in workspace_path.iterdir() if d.is_dir()]
            files = [str(f) for f in workspace_path.rglob("*") if f.is_file()]
            
            workspace_info = WorkspaceInfo(
                root_path=str(workspace_path),
                folders=folders,
                files=files
            )
            
            # Store in context
            ctx.request_context.lifespan_context.active_workspaces[ctx.client_id] = workspace_info
            
            return {
                "success": True,
                "workspace_path": str(workspace_path),
                "folders": len(folders),
                "files": len(files),
                "new_window": new_window
            }
        else:
            return {"error": f"Failed to open VS Code: {result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to open workspace: {str(e)}"}


@mcp.tool(
    name="edit_file",
    title="Edit File",
    description="Edits a file with specified content, supporting create, update, and append operations"
)
async def edit_file(
    file_path: str,
    content: str,
    operation: str = "write",  # write, append, prepend, insert
    line_number: int = 0,
    create_if_not_exists: bool = True
) -> Dict[str, Any]:
    """Edit file content with various operations"""
    try:
        file_path = Path(file_path).expanduser().resolve()
        
        if not file_path.exists():
            if create_if_not_exists:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                return {"error": f"File does not exist: {file_path}"}
        
        if operation == "write":
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        elif operation == "append":
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
        
        elif operation == "prepend":
            with open(file_path, 'r+', encoding='utf-8') as f:
                old_content = f.read()
                f.seek(0)
                f.write(content + old_content)
                f.truncate()
        
        elif operation == "insert":
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if line_number <= len(lines):
                lines.insert(line_number, content + '\n')
            else:
                lines.append(content + '\n')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        stat = file_path.stat()
        return {
            "success": True,
            "file_path": str(file_path),
            "operation": operation,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
        
    except Exception as e:
        return {"error": f"Failed to edit file: {str(e)}"}


@mcp.tool(
    name="read_file",
    title="Read File Content",
    description="Reads file content with options for line ranges and syntax highlighting"
)
async def read_file(
    file_path: str,
    start_line: int = 1,
    end_line: int = None,
    max_lines: int = 1000
) -> Dict[str, Any]:
    """Read file content with line range support"""
    try:
        file_path = Path(file_path).expanduser().resolve()
        
        if not file_path.exists():
            return {"error": f"File does not exist: {file_path}"}
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Adjust line numbers
        start_line = max(1, start_line)
        if end_line is None:
            end_line = min(start_line + max_lines - 1, total_lines)
        else:
            end_line = min(end_line, total_lines)
        
        content_lines = lines[start_line-1:end_line]
        content = ''.join(content_lines)
        
        # Detect language
        extension = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'shell',
            '.yml': 'yaml',
            '.yaml': 'yaml'
        }
        
        language = language_map.get(extension, 'text')
        
        return {
            "content": content,
            "file_path": str(file_path),
            "language": language,
            "total_lines": total_lines,
            "displayed_lines": f"{start_line}-{end_line}",
            "file_size": file_path.stat().st_size
        }
        
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


@mcp.tool(
    name="git_status",
    title="Git Status",
    description="Gets the current git status including branch, modified files, and staged changes"
)
async def git_status(repo_path: str = ".") -> Dict[str, Any]:
    """Get git repository status"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Not a git repository: {repo_path}"}
        
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if branch_result.returncode != 0:
            return {"error": "Failed to get git branch"}
        
        branch = branch_result.stdout.strip()
        
        # Get git status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        # Parse git status
        modified_files = []
        untracked_files = []
        staged_files = []
        
        for line in status_result.stdout.strip().split('\n'):
            if line:
                status = line[:2]
                filename = line[3:]
                
                if status.startswith('M') or status.startswith('A') or status.startswith('D'):
                    staged_files.append(filename)
                elif status.startswith(' M') or status.startswith(' D'):
                    modified_files.append(filename)
                elif status.startswith('??'):
                    untracked_files.append(filename)
        
        # Get remote status
        remote_result = subprocess.run(
            ["git", "rev-list", "--count", "--left-right", "@{u}...HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        commits_ahead = 0
        commits_behind = 0
        
        if remote_result.returncode == 0:
            counts = remote_result.stdout.strip().split('\t')
            if len(counts) == 2:
                commits_behind = int(counts[0])
                commits_ahead = int(counts[1])
        
        git_info = GitInfo(
            branch=branch,
            status="clean" if not modified_files and not untracked_files and not staged_files else "dirty",
            commits_ahead=commits_ahead,
            commits_behind=commits_behind,
            modified_files=modified_files,
            untracked_files=untracked_files,
            staged_files=staged_files
        )
        
        return {
            "branch": git_info.branch,
            "status": git_info.status,
            "commits_ahead": git_info.commits_ahead,
            "commits_behind": git_info.commits_behind,
            "modified_files": git_info.modified_files,
            "untracked_files": git_info.untracked_files,
            "staged_files": git_info.staged_files,
            "repository_path": str(repo_path)
        }
        
    except Exception as e:
        return {"error": f"Failed to get git status: {str(e)}"}


@mcp.tool(
    name="git_commit",
    title="Git Commit",
    description="Commits changes to the git repository with a message"
)
async def git_commit(repo_path: str, message: str, add_all: bool = True) -> Dict[str, Any]:
    """Commit changes to git repository"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Not a git repository: {repo_path}"}
        
        # Add all changes if requested
        if add_all:
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if add_result.returncode != 0:
                return {"error": f"Failed to add files: {add_result.stderr}"}
        
        # Commit changes
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode == 0:
            return {
                "success": True,
                "message": message,
                "repository": str(repo_path),
                "output": commit_result.stdout
            }
        else:
            return {"error": f"Failed to commit: {commit_result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to commit: {str(e)}"}


@mcp.tool(
    name="git_push",
    title="Git Push",
    description="Pushes commits to the remote repository"
)
async def git_push(repo_path: str, remote: str = "origin", branch: str = None) -> Dict[str, Any]:
    """Push commits to remote repository"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Not a git repository: {repo_path}"}
        
        # Get current branch if not specified
        if not branch:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if branch_result.returncode != 0:
                return {"error": "Failed to get current branch"}
            
            branch = branch_result.stdout.strip()
        
        # Push changes
        push_result = subprocess.run(
            ["git", "push", remote, branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode == 0:
            return {
                "success": True,
                "remote": remote,
                "branch": branch,
                "output": push_result.stdout
            }
        else:
            return {"error": f"Failed to push: {push_result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to push: {str(e)}"}


@mcp.tool(
    name="analyze_code",
    title="Analyze Code",
    description="Analyzes code for complexity, issues, and structure"
)
async def analyze_code(file_path: str) -> Dict[str, Any]:
    """Analyze code file for complexity and structure"""
    try:
        file_path = Path(file_path).expanduser().resolve()
        
        if not file_path.exists():
            return {"error": f"File does not exist: {file_path}"}
        
        extension = file_path.suffix.lower()
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Basic analysis
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.html': 'html',
            '.css': 'css'
        }
        
        language = language_map.get(extension, 'text')
        
        # Function extraction (basic)
        functions = []
        imports = []
        issues = []
        
        if extension == '.py':
            # Python analysis
            import_pattern = r'^(import|from)\s+\w+'
            function_pattern = r'^def\s+(\w+)\s*\('
            class_pattern = r'^class\s+(\w+)'
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                if re.match(import_pattern, line):
                    imports.append(line)
                
                func_match = re.match(function_pattern, line)
                if func_match:
                    functions.append({
                        "name": func_match.group(1),
                        "line": i,
                        "type": "function"
                    })
                
                class_match = re.match(class_pattern, line)
                if class_match:
                    functions.append({
                        "name": class_match.group(1),
                        "line": i,
                        "type": "class"
                    })
        
        # Calculate complexity (basic)
        complexity_score = 0
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in ['if', 'elif', 'for', 'while', 'try', 'except', 'with']):
                complexity_score += 1
        
        analysis = {
            "file_path": str(file_path),
            "language": language,
            "total_lines": total_lines,
            "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "complexity_score": complexity_score,
            "functions": functions,
            "imports": imports,
            "issues": issues,
            "file_size": file_path.stat().st_size
        }
        
        return analysis
        
    except Exception as e:
        return {"error": f"Failed to analyze code: {str(e)}"}


@mcp.tool(
    name="run_command",
    title="Run Terminal Command",
    description="Executes a terminal command in the workspace directory"
)
async def run_command(command: str, working_dir: str = ".") -> Dict[str, Any]:
    """Execute terminal command in workspace"""
    try:
        working_dir = Path(working_dir).expanduser().resolve()
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "command": command,
            "working_dir": str(working_dir),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"error": f"Failed to run command: {str(e)}"}


@mcp.tool(
    name="find_files",
    title="Find Files",
    description="Finds files by pattern, extension, or content search"
)
async def find_files(
    pattern: str = None,
    extension: str = None,
    contains_text: str = None,
    directory: str = ".",
    recursive: bool = True
) -> List[Dict[str, Any]]:
    """Find files by various criteria"""
    try:
        directory = Path(directory).expanduser().resolve()
        
        if not directory.exists():
            return [{"error": f"Directory does not exist: {directory}"}]
        
        matches = []
        
        # Determine search method
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.iterdir()
        
        for file_path in files:
            if file_path.is_file():
                match = True
                
                # Filter by pattern
                if pattern and not file_path.match(pattern):
                    match = False
                
                # Filter by extension
                if extension and not file_path.suffix.lower() == extension.lower():
                    match = False
                
                # Filter by content
                if contains_text and match:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        if contains_text.lower() not in content.lower():
                            match = False
                    except:
                        match = False
                
                if match:
                    matches.append({
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "extension": file_path.suffix,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        return matches
        
    except Exception as e:
        return [{"error": f"Failed to find files: {str(e)}"}]


@mcp.tool(
    name="install_extension",
    title="Install VS Code Extension",
    description="Installs a VS Code extension by ID"
)
async def install_extension(extension_id: str) -> Dict[str, Any]:
    """Install VS Code extension"""
    try:
        cmd = ["code", "--install-extension", extension_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                "success": True,
                "extension": extension_id,
                "output": result.stdout
            }
        else:
            return {"error": f"Failed to install extension: {result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to install extension: {str(e)}"}


@mcp.tool(
    name="format_code",
    title="Format Code",
    description="Formats code using appropriate formatter for the language"
)
async def format_code(file_path: str, formatter: str = "auto") -> Dict[str, Any]:
    """Format code file"""
    try:
        file_path = Path(file_path).expanduser().resolve()
        
        if not file_path.exists():
            return {"error": f"File does not exist: {file_path}"}
        
        extension = file_path.suffix.lower()
        
        # Determine formatter based on file extension
        formatters = {
            '.py': 'black',
            '.js': 'prettier',
            '.ts': 'prettier',
            '.json': 'prettier',
            '.html': 'prettier',
            '.css': 'prettier'
        }
        
        if formatter == "auto":
            formatter = formatters.get(extension, None)
        
        if not formatter:
            return {"error": f"No formatter available for {extension} files"}
        
        # Run formatter
        cmd = [formatter, str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                "success": True,
                "file": str(file_path),
                "formatter": formatter,
                "output": result.stdout
            }
        else:
            return {"error": f"Formatter failed: {result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to format code: {str(e)}"}


# The FastMCP instance itself is the ASGI application
app = mcp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gpt_oss_mcp_server.ide_integration_server:app", host="0.0.0.0", port=8004, reload=True)