#!/usr/bin/env python3
"""
GitHub Actions Server (Port 8005)
Provides CI/CD integration and GitHub repository management
"""

import os
import base64
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from logging_config import setup_logger, ServiceMonitor

# Configure logging
logger = setup_logger("github_actions_server")

app = FastAPI(title="GitHub Actions Server", version="1.0.0")

# Initialize ServiceMonitor
monitor = ServiceMonitor("github_actions_server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GitHubConfig(BaseModel):
    token: str
    repository: str
    owner: str

class WorkflowConfig(BaseModel):
    name: str
    on: Dict[str, Any]
    jobs: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    github_api_status: str
    active_workflows: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for GitHub Actions server"""
    monitor.record_request()
    github_status = "unknown"
    try:
        response = requests.get("https://api.github.com/status", timeout=5)
        if response.status_code == 200:
            github_status = "healthy"
            monitor.record_success()
        else:
            github_status = "degraded"
            monitor.record_error(f"GitHub API degraded: {response.status_code}")
    except Exception as e:
        github_status = "unavailable"
        monitor.record_error(f"GitHub API unavailable: {e}")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        github_api_status=github_status,
        active_workflows=0  # Would track active workflows
    )

@app.post("/repository/info")
async def get_repository_info(config: GitHubConfig):
    """Get repository information"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to get repository info: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to get repository info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PullRequest(BaseModel):
    title: str
    head: str
    base: str
    body: Optional[str] = None

@app.post("/pulls/create")
async def create_pull_request(config: GitHubConfig, pr: PullRequest):
    """Create a pull request in the repository"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/pulls"

        payload = pr.dict(exclude_unset=True)

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to create pull request: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to create pull request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pulls/list")
async def list_pull_requests(config: GitHubConfig, state: Optional[str] = "open"):
    """List pull requests in the repository"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/pulls?state={state}"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to list pull requests: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to list pull requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class Issue(BaseModel):
    title: str
    body: Optional[str] = None
    labels: Optional[List[str]] = None

@app.post("/issues/create")
async def create_issue(config: GitHubConfig, issue: Issue):
    """Create an issue in the repository"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/issues"

        payload = issue.dict(exclude_unset=True)

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to create issue: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to create issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issues/list")
async def list_issues(config: GitHubConfig, state: Optional[str] = "open"):
    """List issues in the repository"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/issues?state={state}"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to list issues: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to list issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cicd/cancel_workflow")
async def cancel_workflow(config: GitHubConfig, run_id: str):
    """Cancel a workflow run"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/runs/{run_id}/cancel"

        response = requests.post(url, headers=headers)

        if response.status_code == 202:
            monitor.record_success()
            return {"success": True, "message": f"Workflow run {run_id} cancellation requested."}
        else:
            monitor.record_error(f"Failed to cancel workflow: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cicd/rerun_workflow")
async def rerun_workflow(config: GitHubConfig, run_id: str):
    """Re-run a workflow"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/runs/{run_id}/rerun"

        response = requests.post(url, headers=headers)

        if response.status_code == 204:
            monitor.record_success()
            return {"success": True, "message": f"Workflow run {run_id} re-queued successfully."}
        else:
            monitor.record_error(f"Failed to re-run workflow: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to re-run workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cicd/workflow_run")
async def get_workflow_run(config: GitHubConfig, run_id: str):
    """Get a specific workflow run"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/runs/{run_id}"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to get workflow run: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to get workflow run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/repository/delete_file")
async def delete_repository_file(config: GitHubConfig, file_path: str):
    """Delete a file in the repository"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/contents/{file_path}"

        # Get SHA of the file to be deleted
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json().get("sha")
        else:
            monitor.record_error(f"File not found or unable to retrieve SHA: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )

        payload = {
            "message": f"Delete file {file_path}",
            "sha": sha,
            "branch": "main"
        }

        response = requests.delete(url, headers=headers, json=payload)

        if response.status_code == 200:
            monitor.record_success()
            return {
                "success": True,
                "message": f"File {file_path} deleted successfully.",
                "github_response": response.json()
            }
        else:
            monitor.record_error(f"Failed to delete file: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/repository/create_file")
async def create_repository_file(config: GitHubConfig, file_path: str, content: str):
    """Create a new file in the repository"""
    monitor.record_request()
    try:
        encoded_content = base64.b64encode(content.encode()).decode()

        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/contents/{file_path}"

        # Check if file exists to get SHA for update
        response = requests.get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get("sha")

        payload = {
            "message": f"Create/Update file {file_path}",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            monitor.record_success()
            return {
                "success": True,
                "message": f"File {file_path} created/updated successfully.",
                "github_response": response.json()
            }
        else:
            monitor.record_error(f"Failed to create/update file: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to create/update file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows/list")
async def list_workflows(config: GitHubConfig):
    """List all workflows in the repository"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/workflows"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to list workflows: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows/runs")
async def get_workflow_runs(config: GitHubConfig, workflow_id: Optional[str] = None):
    """Get workflow runs"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        if workflow_id:
            url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/runs"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            monitor.record_success()
            return response.json()
        else:
            monitor.record_error(f"Failed to get workflow runs: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to get workflow runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows/trigger")
async def trigger_workflow(config: GitHubConfig, workflow_id: str, inputs: Optional[Dict[str, Any]] = None):
    """Trigger a workflow"""
    monitor.record_request()
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/actions/workflows/{workflow_id}/dispatches"
        
        payload = {
            "ref": "main",
            "inputs": inputs or {}
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            monitor.record_success()
            return {"status": "triggered", "workflow_id": workflow_id}
        else:
            monitor.record_error(f"Failed to trigger workflow: {response.status_code} - {response.json() if response.content else 'No content'}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json() if response.content else "Failed to trigger workflow"
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to trigger workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows/create")
async def create_workflow(config: GitHubConfig, workflow_config: WorkflowConfig):
    """Create a new GitHub Actions workflow"""
    monitor.record_request()
    try:
        # Create workflow file
        workflow_filename = f"{workflow_config.name}.yml"
        workflow_content = f"name: {workflow_config.name}\n\n" \
                           f"on:\n"
        for key, value in workflow_config.on.items():
            workflow_content += f"  {key}: "
            if isinstance(value, dict):
                workflow_content += "\n"
                for sub_key, sub_value in value.items():
                    workflow_content += f"    {sub_key}: {sub_value}\n"
            else:
                workflow_content += f"{value}\n"

        workflow_content += f"jobs:\n"
        for job_name, job_details in workflow_config.jobs.items():
            workflow_content += f"  {job_name}:\n"
            for detail_key, detail_value in job_details.items():
                if isinstance(detail_value, dict):
                    workflow_content += f"    {detail_key}:\n"
                    for sub_key, sub_value in detail_value.items():
                        if isinstance(sub_value, list):
                            workflow_content += f"      {sub_key}:\n"
                            for item in sub_value:
                                if isinstance(item, dict):
                                    workflow_content += f"        - {json.dumps(item)}\n"
                                else:
                                    workflow_content += f"        - {item}\n"
                        else:
                            workflow_content += f"      {sub_key}: {json.dumps(sub_value)}\n"
                else:
                    workflow_content += f"    {detail_key}: {detail_value}\n"

        encoded_content = base64.b64encode(workflow_content.encode()).decode()

        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/contents/{workflow_filename}"

        # Check if file exists to get SHA for update
        response = requests.get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get("sha")

        payload = {
            "message": f"Create/Update workflow {workflow_config.name}",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            monitor.record_success()
            return {
                "success": True,
                "message": f"Workflow {workflow_config.name} created/updated successfully.",
                "file_path": workflow_filename,
                "github_response": response.json()
            }
        else:
            monitor.record_error(f"Failed to create/update workflow: {response.status_code} - {response.json()}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to create/update workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        workflow_content = f"""name: {workflow_config.name}

on:
{json.dumps(workflow_config.on, indent=2)}

jobs:
{json.dumps(workflow_config.jobs, indent=2)}
"""
        
        # This would typically commit to GitHub
        # For now, return the generated content
        monitor.record_success()
        return {
            "workflow_content": workflow_content,
            "file_path": f".github/workflows/{workflow_config.name.lower().replace(' ', '_')}.yml"
        }
    except Exception as e:
        monitor.record_error(e)
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows/create_and_push")
async def create_and_push_workflow(config: GitHubConfig, workflow_config: WorkflowConfig, commit_message: str = "Add new workflow"):
    """Create a new GitHub Actions workflow and push it to the repository"""
    try:
        workflow_content = f"""name: {workflow_config.name}

on:
{json.dumps(workflow_config.on, indent=2)}

jobs:
{json.dumps(workflow_config.jobs, indent=2)}
"""
        
        file_path = f".github/workflows/{workflow_config.name.lower().replace(' ', '_')}.yml"
        
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if file exists to decide between PUT (update) or POST (create)
        get_file_url = f"https://api.github.com/repos/{config.owner}/{config.repository}/contents/{file_path}"
        get_response = requests.get(get_file_url, headers=headers)
        
        sha = None
        if get_response.status_code == 200:
            sha = get_response.json().get("sha")

        create_update_url = f"https://api.github.com/repos/{config.owner}/{config.repository}/contents/{file_path}"
        
        payload = {
            "message": commit_message,
            "content": base64.b64encode(workflow_content.encode()).decode(),
            "branch": "main" # Assuming 'main' branch, can be made configurable
        }
        if sha:
            payload["sha"] = sha

        put_response = requests.put(create_update_url, headers=headers, json=payload)
        
        if put_response.status_code in [200, 201]:
            return {"status": "success", "message": "Workflow created/updated and pushed", "file_path": file_path, "response": put_response.json()}
        else:
            raise HTTPException(
                status_code=put_response.status_code,
                detail=put_response.json() if put_response.content else "Failed to create/update workflow file"
            )
    except Exception as e:
        logger.error(f"Failed to create and push workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pull_requests/create")
async def create_pull_request(config: GitHubConfig, title: str, head: str, base: str, body: Optional[str] = None):
    """Create a new pull request"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/pulls"
        
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json() if response.content else "Failed to create pull request"
            )
    except Exception as e:
        logger.error(f"Failed to create pull request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pull_requests/list")
async def list_pull_requests(config: GitHubConfig, state: Optional[str] = "open"):
    """List pull requests in the repository"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/pulls?state={state}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json() if response.content else "Failed to list pull requests"
            )
    except Exception as e:
        logger.error(f"Failed to list pull requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pull_requests/merge")
async def merge_pull_request(config: GitHubConfig, pull_number: int, commit_title: Optional[str] = None, commit_message: Optional[str] = None, merge_method: str = "merge"):
    """Merge a pull request"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/pulls/{pull_number}/merge"
        
        payload = {
            "commit_title": commit_title,
            "commit_message": commit_message,
            "merge_method": merge_method # Can be 'merge', 'squash', or 'rebase'
        }
        
        response = requests.put(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json() if response.content else "Failed to merge pull request"
            )
    except Exception as e:
        logger.error(f"Failed to merge pull request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/branches/create")
async def create_branch(config: GitHubConfig, branch_name: str, source_branch: str = "main"):
    """Create a new branch from a source branch"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get the SHA of the source branch
        ref_url = f"https://api.github.com/repos/{config.owner}/{config.repository}/git/ref/heads/{source_branch}"
        ref_response = requests.get(ref_url, headers=headers)
        
        if ref_response.status_code != 200:
            raise HTTPException(
                status_code=ref_response.status_code,
                detail=ref_response.json() if ref_response.content else f"Failed to get SHA for source branch {source_branch}"
            )
        
        source_sha = ref_response.json()["object"]["sha"]
        
        # Create the new branch
        create_branch_url = f"https://api.github.com/repos/{config.owner}/{config.repository}/git/refs"
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": source_sha
        }
        
        create_response = requests.post(create_branch_url, headers=headers, json=payload)
        
        if create_response.status_code == 201:
            return create_response.json()
        else:
            raise HTTPException(
                status_code=create_response.status_code,
                detail=create_response.json() if create_response.content else "Failed to create branch"
            )
    except Exception as e:
        logger.error(f"Failed to create branch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/branches/delete")
async def delete_branch(config: GitHubConfig, branch_name: str):
    """Delete a branch from the repository"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/git/refs/heads/{branch_name}"
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204: # 204 No Content indicates successful deletion
            return {"status": "success", "message": f"Branch '{branch_name}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json() if response.content else "Failed to delete branch"
            )
    except Exception as e:
        logger.error(f"Failed to delete branch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/branches/list")
async def list_branches(config: GitHubConfig):
    """List repository branches"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/branches"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        logger.error(f"Failed to list branches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pulls/list")
async def list_pull_requests(config: GitHubConfig, state: str = "open"):
    """List pull requests"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/pulls"
        params = {"state": state}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        logger.error(f"Failed to list pull requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/issues/list")
async def list_issues(config: GitHubConfig, state: str = "open"):
    """List repository issues"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/issues"
        params = {"state": state}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        logger.error(f"Failed to list issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deployments/list")
async def list_deployments(config: GitHubConfig):
    """List deployments"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/deployments"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/release/create")
async def create_release(config: GitHubConfig, tag_name: str, name: str, body: str):
    """Create a new release"""
    try:
        headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{config.owner}/{config.repository}/releases"
        payload = {
            "tag_name": tag_name,
            "name": name,
            "body": body,
            "draft": False,
            "prerelease": False
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )
    except Exception as e:
        logger.error(f"Failed to create release: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)