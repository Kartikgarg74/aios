from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
import os
import subprocess
import tempfile
import time

app = FastAPI()
mcp = FastMCP(app, name="github")

class Repository(BaseModel):
    name: str
    owner: str
    description: str
    stars: int
    forks: int
    last_updated: str
    clone_url: str

class PullRequest(BaseModel):
    id: int
    title: str
    state: str
    created_at: str
    user: str

class Commit(BaseModel):
    sha: str
    message: str
    author: str
    date: str

# Mock data for demo purposes
mock_repos = [
    Repository(
        name="gpt-oss",
        owner="ai-organization",
        description="GPT-powered Operating System",
        stars=42,
        forks=12,
        last_updated="2023-06-15T14:32:00Z",
        clone_url="https://github.com/ai-organization/gpt-oss.git"
    ),
    Repository(
        name="fastmcp",
        owner="ai-organization",
        description="Fast Multi-Channel Protocol",
        stars=24,
        forks=6,
        last_updated="2023-06-10T09:15:00Z",
        clone_url="https://github.com/ai-organization/fastmcp.git"
    )
]

mock_prs = {
    "ai-organization/gpt-oss": [
        PullRequest(
            id=1,
            title="Add dark mode support",
            state="open",
            created_at="2023-06-14T10:30:00Z",
            user="dev1"
        ),
        PullRequest(
            id=2,
            title="Fix memory leak",
            state="closed",
            created_at="2023-06-12T15:45:00Z",
            user="dev2"
        )
    ]
}

@mcp.tool()
async def list_repositories() -> List[Repository]:
    """List all repositories accessible with the current credentials."""
    # In a real implementation, this would call the GitHub API
    return mock_repos

@mcp.tool()
async def list_pull_requests(repo: str) -> List[PullRequest]:
    """List pull requests for a specific repository."""
    # In a real implementation, this would call the GitHub API
    return mock_prs.get(repo, [])

@mcp.tool()
async def clone_repository(url: str, local_path: str) -> bool:
    """Clone a GitHub repository to a local path."""
    try:
        subprocess.run(["git", "clone", url, local_path], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@mcp.tool()
async def create_pull_request(
    repo: str, 
    title: str, 
    head: str, 
    base: str, 
    body: Optional[str] = None
) -> PullRequest:
    """Create a new pull request."""
    # In a real implementation, this would call the GitHub API
    new_pr = PullRequest(
        id=int(time.time()),
        title=title,
        state="open",
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        user="current-user"
    )
    
    if repo not in mock_prs:
        mock_prs[repo] = []
    mock_prs[repo].append(new_pr)
    
    return new_pr

@mcp.tool()
async def get_commits(repo: str, branch: str = "main", limit: int = 10) -> List[Commit]:
    """Get recent commits for a repository."""
    # In a real implementation, this would call the GitHub API or local git
    return [
        Commit(
            sha="abc123",
            message="Initial commit",
            author="dev1",
            date="2023-06-01T12:00:00Z"
        ),
        Commit(
            sha="def456",
            message="Add basic functionality",
            author="dev2",
            date="2023-06-02T14:30:00Z"
        )
    ][:limit]

@mcp.tool()
async def create_repository(name: str, description: str, private: bool = False) -> Repository:
    """Create a new GitHub repository."""
    # In a real implementation, this would call the GitHub API
    new_repo = Repository(
        name=name,
        owner="current-user",
        description=description,
        stars=0,
        forks=0,
        last_updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        clone_url=f"https://github.com/current-user/{name}.git"
    )
    mock_repos.append(new_repo)
    return new_repo

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)