"""
GitHub Actions Server for AI Operating System
Port: 8005
Handles CI/CD workflows, repository management, GitHub API integration,
automated testing, deployment pipelines, and GitHub Actions orchestration.
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import datetime
import re

from mcp.server.fastmcp import Context, FastMCP


@dataclass
class RepositoryInfo:
    """GitHub repository information"""
    name: str
    owner: str
    description: str
    url: str
    default_branch: str
    private: bool
    stars: int
    forks: int
    language: str
    size: int


@dataclass
class WorkflowInfo:
    """GitHub Actions workflow information"""
    id: str
    name: str
    path: str
    state: str
    created_at: str
    updated_at: str
    badge_url: str


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run"""
    id: str
    name: str
    status: str
    conclusion: str
    branch: str
    commit_sha: str
    commit_message: str
    created_at: str
    updated_at: str
    duration: str


@dataclass
class PullRequest:
    """Pull request information"""
    number: int
    title: str
    state: str
    author: str
    branch: str
    target_branch: str
    description: str
    created_at: str
    updated_at: str
    mergeable: bool
    checks_status: str


@dataclass
class Issue:
    """GitHub issue information"""
    number: int
    title: str
    state: str
    author: str
    assignees: List[str]
    labels: List[str]
    description: str
    created_at: str
    updated_at: str


@dataclass
class AppContext:
    """Application context for GitHub operations"""
    active_repos: Dict[str, RepositoryInfo] = field(default_factory=dict)
    recent_workflows: List[WorkflowRun] = field(default_factory=list)
    github_token: Optional[str] = None
    
    def get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment"""
        return self.github_token or os.getenv('GITHUB_TOKEN')


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle"""
    context = AppContext()
    try:
        yield context
    finally:
        # Cleanup
        context.active_repos.clear()
        context.recent_workflows.clear()


# Create the FastMCP server
mcp = FastMCP(
    name="github_actions",
    instructions="""
    GitHub Actions Server for AI Operating System.
    
    This server provides comprehensive GitHub integration including:
    - Repository management and cloning
    - Workflow execution and monitoring
    - Pull request automation
    - Issue management
    - CI/CD pipeline control
    - GitHub API interactions
    - Automated testing and deployment
    
    Requires GITHUB_TOKEN environment variable for API access.
    """.strip(),
    lifespan=app_lifespan,
    port=8005,
)


@mcp.tool(
    name="clone_repository",
    title="Clone GitHub Repository",
    description="Clones a GitHub repository to the specified directory"
)
async def clone_repository(
    repo_url: str,
    target_dir: str = None,
    branch: str = "main"
) -> Dict[str, Any]:
    """Clone GitHub repository"""
    try:
        # Parse repository name from URL
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        if target_dir:
            target_path = Path(target_dir).expanduser().resolve() / repo_name
        else:
            target_path = Path.cwd() / repo_name
        
        # Clone repository
        cmd = ["git", "clone", "--branch", branch, repo_url, str(target_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get repository info
            os.chdir(target_path)
            
            # Get remote URL
            remote_result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True
            )
            
            # Get branch info
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True
            )
            
            return {
                "success": True,
                "repository": repo_name,
                "branch": branch,
                "target_path": str(target_path),
                "remote_url": remote_result.stdout.strip() if remote_result.returncode == 0 else repo_url,
                "current_branch": branch_result.stdout.strip() if branch_result.returncode == 0 else branch
            }
        else:
            return {"error": f"Failed to clone repository: {result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to clone repository: {str(e)}"}


@mcp.tool(
    name="list_workflows",
    title="List GitHub Actions Workflows",
    description="Lists all GitHub Actions workflows in the repository"
)
async def list_workflows(repo_path: str = ".") -> List[Dict[str, Any]]:
    """List GitHub Actions workflows"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        workflows_dir = repo_path / ".github" / "workflows"
        
        if not workflows_dir.exists():
            return [{"info": "No GitHub Actions workflows found"}]
        
        workflows = []
        for workflow_file in workflows_dir.glob("*.yml"):
            if workflow_file.is_file():
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract workflow name
                name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
                workflow_name = name_match.group(1).strip() if name_match else workflow_file.stem
                
                # Get file stats
                stat = workflow_file.stat()
                
                workflows.append({
                    "name": workflow_name,
                    "file": str(workflow_file.relative_to(repo_path)),
                    "path": str(workflow_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "content": content
                })
        
        return workflows
        
    except Exception as e:
        return [{"error": f"Failed to list workflows: {str(e)}"}]


@mcp.tool(
    name="create_workflow",
    title="Create GitHub Actions Workflow",
    description="Creates a new GitHub Actions workflow file"
)
async def create_workflow(
    repo_path: str,
    workflow_name: str,
    content: str,
    trigger: str = "push"
) -> Dict[str, Any]:
    """Create GitHub Actions workflow"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        workflows_dir = repo_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{workflow_name.lower().replace(' ', '_')}.yml"
        workflow_path = workflows_dir / filename
        
        # Create workflow content if not provided
        if not content:
            content = f"""name: {workflow_name}

on:
  {trigger}:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up environment
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm install
    
    - name: Run tests
      run: npm test
    
    - name: Build
      run: npm run build
"""
        
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "workflow_name": workflow_name,
            "file": str(workflow_path),
            "trigger": trigger
        }
        
    except Exception as e:
        return {"error": f"Failed to create workflow: {str(e)}"}


@mcp.tool(
    name="run_tests",
    title="Run Tests",
    description="Runs automated tests in the repository"
)
async def run_tests(
    repo_path: str,
    test_command: str = None,
    test_type: str = "auto"
) -> Dict[str, Any]:
    """Run automated tests"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        # Auto-detect test command
        if not test_command:
            if (repo_path / "package.json").exists():
                test_command = "npm test"
            elif (repo_path / "pytest.ini").exists() or (repo_path / "tests").exists():
                test_command = "python -m pytest"
            elif (repo_path / "requirements.txt").exists():
                test_command = "python -m unittest discover"
            elif (repo_path / "Makefile").exists():
                test_command = "make test"
            else:
                return {"error": "Could not auto-detect test command"}
        
        # Run tests
        result = subprocess.run(
            test_command,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        # Parse test results (basic)
        output = result.stdout + result.stderr
        
        # Count passed/failed tests (basic parsing)
        passed = len(re.findall(r'(PASSED|passed|✓)', output, re.IGNORECASE))
        failed = len(re.findall(r'(FAILED|failed|✗|ERROR)', output, re.IGNORECASE))
        
        return {
            "success": result.returncode == 0,
            "command": test_command,
            "passed": passed,
            "failed": failed,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": "completed"
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Tests timed out after 5 minutes"}
    except Exception as e:
        return {"error": f"Failed to run tests: {str(e)}"}


@mcp.tool(
    name="build_project",
    title="Build Project",
    description="Builds the project using appropriate build system"
)
async def build_project(
    repo_path: str,
    build_command: str = None
) -> Dict[str, Any]:
    """Build the project"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        # Auto-detect build command
        if not build_command:
            if (repo_path / "package.json").exists():
                build_command = "npm run build"
            elif (repo_path / "setup.py").exists():
                build_command = "python setup.py build"
            elif (repo_path / "Makefile").exists():
                build_command = "make"
            elif (repo_path / "build.gradle").exists():
                build_command = "./gradlew build"
            elif (repo_path / "pom.xml").exists():
                build_command = "mvn clean install"
            else:
                return {"error": "Could not auto-detect build command"}
        
        # Run build
        result = subprocess.run(
            build_command,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        return {
            "success": result.returncode == 0,
            "command": build_command,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": "completed"
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Build timed out after 10 minutes"}
    except Exception as e:
        return {"error": f"Failed to build project: {str(e)}"}


@mcp.tool(
    name="deploy_to_github_pages",
    title="Deploy to GitHub Pages",
    description="Deploys the built project to GitHub Pages"
)
async def deploy_to_github_pages(
    repo_path: str,
    build_dir: str = "dist",
    branch: str = "gh-pages"
) -> Dict[str, Any]:
    """Deploy to GitHub Pages"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        build_path = repo_path / build_dir
        
        if not build_path.exists():
            return {"error": f"Build directory does not exist: {build_dir}"}
        
        # Check if gh-pages branch exists
        check_branch = subprocess.run(
            ["git", "branch", "--list", branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if branch not in check_branch.stdout:
            # Create gh-pages branch
            subprocess.run(["git", "checkout", "--orphan", branch], cwd=repo_path)
            subprocess.run(["git", "rm", "-rf", "."], cwd=repo_path)
        else:
            subprocess.run(["git", "checkout", branch], cwd=repo_path)
        
        # Copy build files
        import shutil
        for item in build_path.iterdir():
            if item.is_file():
                shutil.copy2(item, repo_path)
            elif item.is_dir():
                shutil.copytree(item, repo_path / item.name, dirs_exist_ok=True)
        
        # Commit and push
        subprocess.run(["git", "add", "."], cwd=repo_path)
        subprocess.run(
            ["git", "commit", "-m", f"Deploy to GitHub Pages - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            cwd=repo_path
        )
        subprocess.run(["git", "push", "origin", branch], cwd=repo_path)
        
        # Switch back to main
        subprocess.run(["git", "checkout", "main"], cwd=repo_path)
        
        return {
            "success": True,
            "branch": branch,
            "build_dir": build_dir,
            "repository": str(repo_path)
        }
        
    except Exception as e:
        return {"error": f"Failed to deploy to GitHub Pages: {str(e)}"}


@mcp.tool(
    name="create_pull_request",
    title="Create Pull Request",
    description="Creates a pull request from the current branch"
)
async def create_pull_request(
    repo_path: str,
    title: str,
    description: str,
    base_branch: str = "main",
    head_branch: str = None
) -> Dict[str, Any]:
    """Create a pull request"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        # Get current branch if not specified
        if not head_branch:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if branch_result.returncode != 0:
                return {"error": "Failed to get current branch"}
            
            head_branch = branch_result.stdout.strip()
        
        # Push the branch
        push_result = subprocess.run(
            ["git", "push", "origin", head_branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            return {"error": f"Failed to push branch: {push_result.stderr}"}
        
        # Create PR using GitHub CLI (if available)
        pr_cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", description,
            "--base", base_branch,
            "--head", head_branch
        ]
        
        pr_result = subprocess.run(
            pr_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if pr_result.returncode == 0:
            return {
                "success": True,
                "title": title,
                "branch": head_branch,
                "base_branch": base_branch,
                "output": pr_result.stdout
            }
        else:
            return {"error": f"Failed to create PR: {pr_result.stderr}"}
            
    except Exception as e:
        return {"error": f"Failed to create pull request: {str(e)}"}


@mcp.tool(
    name="check_workflow_status",
    title="Check Workflow Status",
    description="Checks the status of GitHub Actions workflows"
)
async def check_workflow_status(repo_path: str = ".") -> List[Dict[str, Any]]:
    """Check workflow status using GitHub CLI"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        # Get workflow runs
        cmd = ["gh", "run", "list", "--limit", "10", "--json", "databaseId,workflowName,status,conclusion,branch,headSha,createdAt,updatedAt"]
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return [{"error": f"Failed to get workflow status: {result.stderr}"}]
        
        try:
            runs = json.loads(result.stdout)
            return runs
        except json.JSONDecodeError:
            return [{"error": "Failed to parse workflow status"}]
        
    except Exception as e:
        return [{"error": f"Failed to check workflow status: {str(e)}"}]


@mcp.tool(
    name="setup_ci_cd",
    title="Setup CI/CD Pipeline",
    description="Sets up a complete CI/CD pipeline for the repository"
)
async def setup_ci_cd(
    repo_path: str,
    project_type: str = "auto",
    include_tests: bool = True,
    include_deployment: bool = True
) -> Dict[str, Any]:
    """Setup complete CI/CD pipeline"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        # Auto-detect project type
        if project_type == "auto":
            if (repo_path / "package.json").exists():
                project_type = "nodejs"
            elif (repo_path / "requirements.txt").exists():
                project_type = "python"
            elif (repo_path / "pom.xml").exists():
                project_type = "java"
            elif (repo_path / "build.gradle").exists():
                project_type = "gradle"
            else:
                project_type = "generic"
        
        # Create workflow based on project type
        workflow_name = f"CI/CD - {project_type.title()}"
        
        if project_type == "nodejs":
            workflow_content = f"""name: {workflow_name}

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Run linting
      run: npm run lint
    
    - name: Build
      run: npm run build

  {'deploy:' if include_deployment else '# deploy:'}
    {'needs: test' if include_deployment else '#   needs: test'}
    {'runs-on: ubuntu-latest' if include_deployment else '#   runs-on: ubuntu-latest'}
    {'if: github.ref == \"refs/heads/main\"' if include_deployment else '#   if: github.ref == "refs/heads/main"'}
    
    {'steps:' if include_deployment else '#   steps:'}
    {'- uses: actions/checkout@v3' if include_deployment else '#   - uses: actions/checkout@v3'}
    {'- name: Deploy to production' if include_deployment else '#   - name: Deploy to production'}
      {'run: echo "Deploying to production..."' if include_deployment else '#     run: echo "Deploying to production..."'}
"""
        elif project_type == "python":
            workflow_content = f"""name: {workflow_name}

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=./ --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  {'deploy:' if include_deployment else '# deploy:'}
    {'needs: test' if include_deployment else '#   needs: test'}
    {'runs-on: ubuntu-latest' if include_deployment else '#   runs-on: ubuntu-latest'}
    {'if: github.ref == \"refs/heads/main\"' if include_deployment else '#   if: github.ref == "refs/heads/main"'}
    
    {'steps:' if include_deployment else '#   steps:'}
    {'- uses: actions/checkout@v3' if include_deployment else '#   - uses: actions/checkout@v3'}
    {'- name: Deploy to production' if include_deployment else '#   - name: Deploy to production'}
      {'run: echo "Deploying to production..."' if include_deployment else '#     run: echo "Deploying to production..."'}
"""
        else:
            workflow_content = f"""name: {workflow_name}

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup environment
      run: |
        echo "Setting up environment..."
        echo "Project type: {project_type}"
    
    - name: Build
      run: |
        echo "Building project..."
        echo "This is a placeholder for {project_type} build"

  {'deploy:' if include_deployment else '# deploy:'}
    {'needs: build' if include_deployment else '#   needs: build'}
    {'runs-on: ubuntu-latest' if include_deployment else '#   runs-on: ubuntu-latest'}
    {'if: github.ref == \"refs/heads/main\"' if include_deployment else '#   if: github.ref == "refs/heads/main"'}
    
    {'steps:' if include_deployment else '#   steps:'}
    {'- uses: actions/checkout@v3' if include_deployment else '#   - uses: actions/checkout@v3'}
    {'- name: Deploy to production' if include_deployment else '#   - name: Deploy to production'}
      {'run: echo "Deploying to production..."' if include_deployment else '#     run: echo "Deploying to production..."'}
"""
        
        # Create workflow
        return await create_workflow(
            repo_path=str(repo_path),
            workflow_name=workflow_name,
            content=workflow_content
        )
        
    except Exception as e:
        return {"error": f"Failed to setup CI/CD: {str(e)}"}


@mcp.tool(
    name="get_repository_info",
    title="Get Repository Information",
    description="Gets detailed information about the repository"
)
async def get_repository_info(repo_path: str = ".") -> Dict[str, Any]:
    """Get comprehensive repository information"""
    try:
        repo_path = Path(repo_path).expanduser().resolve()
        
        # Get git info
        remote_url = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        commit_count = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        # Count files
        all_files = list(repo_path.rglob("*"))
        total_files = len([f for f in all_files if f.is_file()])
        
        # Detect languages
        extensions = {}
        for file in repo_path.rglob("*"):
            if file.is_file():
                ext = file.suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
        
        # Get workflow info
        workflows = await list_workflows(str(repo_path))
        
        return {
            "repository_path": str(repo_path),
            "remote_url": remote_url.stdout.strip() if remote_url.returncode == 0 else None,
            "current_branch": branch.stdout.strip() if branch.returncode == 0 else None,
            "total_commits": int(commit_count.stdout.strip()) if commit_count.returncode == 0 else 0,
            "total_files": total_files,
            "file_extensions": extensions,
            "workflows": workflows,
            "has_github_actions": len([w for w in workflows if "error" not in w]) > 0
        }
        
    except Exception as e:
        return {"error": f"Failed to get repository info: {str(e)}"}


# The FastMCP instance itself is the ASGI application
app = mcp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gpt_oss_mcp_server.github_actions_server:app", host="0.0.0.0", port=8005, reload=True)