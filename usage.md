# Usage Guide for MCP Servers

This document provides a comprehensive guide on how to use, deploy, and understand the features of the MCP (Multi-Component Protocol) servers for the `gpt-oss` reference tools.

## Table of Contents
1.  [Introduction](#introduction)
2.  [Features](#features)
3.  [Getting Started](#getting-started)
    *   [Prerequisites](#prerequisites)
    *   [Building and Running with Docker Compose](#building-and-running-with-docker-compose)
    *   [Manual Server Startup (Advanced)](#manual-server-startup-advanced)
4.  [Service Endpoints](#service-endpoints)
5.  [Troubleshooting](#troubleshooting)

## 1. Introduction

This project provides a set of MCP servers designed to integrate with the `gpt-oss` reference tools, enabling modular and scalable AI application development. Each server handles specific functionalities, communicating via Redis for message queuing and exposing their capabilities through FastAPI endpoints.

## 2. Features

The project comprises several key services, each with distinct features:

*   **Redis**: A high-performance in-memory data store used for message queuing and inter-service communication.
*   **Python Server (Port 8000)**: A general-purpose Python server for executing various Python-based tools and functionalities.
*   **Browser Server (Port 8001)**: Manages browser-related operations, potentially for web scraping, automation, or interacting with web content.
*   **System Operations Server (Port 8002)**: Provides system-level information and control, including CPU, memory, process management, disk usage, and network statistics. It can also attempt to restart services or schedule system shutdowns (requires appropriate permissions).
*   **Communication Server (Port 8003)**: Handles real-time communication, messaging, and contact management. It includes tools for sending messages, retrieving message history, adding contacts, and marking messages as read, with WebSocket support for live updates.
*   **IDE Integration Server (Port 8004)**: Facilitates integration with Integrated Development Environments, likely for code analysis, project management, or development workflows.
*   **GitHub Actions Server (Port 8005)**: Interacts with GitHub, enabling automation of tasks, repository management, or CI/CD pipeline integration.
*   **Voice/UI Server (Port 8006)**: Manages voice-based interactions and user interface elements, potentially for voice commands, text-to-speech, or speech-to-text functionalities.
*   **Marketplace Server (Port 8007)**: Manages the installation, verification, and updating of various components and tools within the AIOS ecosystem.
*   **Orchestrator (Port 9000)**: The central component that coordinates and manages interactions between all other MCP servers.
*   **Frontend (Port 3000)**: A React-based web application that provides a user interface to interact with the various backend services.

## 3. Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Building and Running with Docker Compose

The recommended way to run the entire project is using Docker Compose. This will build all necessary Docker images and start the services in their respective containers.

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Build the Docker images:**
    ```bash
    docker-compose build
    ```
    This command will build all service images defined in `docker-compose.yml`. It might take some time on the first run.

3.  **Start the services:**
    ```bash
    docker-compose up
    ```
    To run services in detached mode (in the background):
    ```bash
    docker-compose up -d
    ```

4.  **Access the Frontend:**
    Once all services are up and running, you can access the frontend application in your web browser at `http://localhost:3000`.

5.  **Stop the services:**
    To stop and remove the containers, networks, and volumes created by `docker-compose up`:
    ```bash
    docker-compose down
    ```

### Manual Server Startup (Advanced)

For development or debugging purposes, you might want to run individual servers manually. This requires a Python environment and specific dependencies.

1.  **Install Python dependencies:**
    Each server has its own `requirements-<service>.txt` file. You'll need to install these for the specific server you want to run.
    For example, for the Python server:
    ```bash
    pip install -r requirements.txt
    ```
    For the Communication server:
    ```bash
    pip install -r requirements-communication.txt
    ```
    And for the System Operations server:
    ```bash
    pip install -r requirements-system.txt
    ```

2.  **Start a Redis instance:**
    If you're not using Docker Compose, you'll need a running Redis instance. You can run it via Docker:
    ```bash
    docker run --name my-redis -p 6379:6379 -d redis:7-alpine
    ```

3.  **Run individual servers:**
    Each server can be started using `uvicorn` (assuming it's installed via its requirements file).
    
    *   **Python Server:**
        ```bash
        uvicorn gpt_oss_mcp_server.python_server:app --host 0.0.0.0 --port 8000
        ```
    *   **Communication Server:**
        ```bash
        uvicorn communication_server:app --host 0.0.0.0 --port 8003
        ```
    *   **System Operations Server:**
        ```bash
        uvicorn system_server:app --host 0.0.0.0 --port 8002
        ```
    *   **Other Servers:**
        Follow a similar pattern for other servers, replacing the module and port as appropriate (refer to `docker-compose.yml` and the respective `Dockerfile.<service>` for the correct entry point and port).

## 4. Service Endpoints

All services expose a `/health` endpoint for health checks. The primary API endpoints and WebSocket connections are as follows:

*   **Redis**: `redis://localhost:6379`
*   **Python Server**: `http://localhost:8000`
*   **Browser Server**: `http://localhost:8001`
*   **System Operations Server**: `http://localhost:8002`
*   **Communication Server**: `http://localhost:8003` (with WebSocket at `/ws/{client_id}`)
*   **IDE Integration Server**: `http://localhost:8004`
*   **GitHub Actions Server**: `http://localhost:8005`
*   **Voice/UI Server**: `http://localhost:8006`
*   **Marketplace Server**: `http://localhost:8007`
*   **Orchestrator**: `http://localhost:9000`
*   **Frontend**: `http://localhost:3000`

## Development and Maintenance Tools

To assist with development and maintenance tasks, a `dev_tools.py` script is available in the `scripts` directory. This script can be used for various cleanup and utility operations.

### Running Development Tools

To run the development tools, navigate to the project root directory and execute the following command:

```bash
python scripts/dev_tools.py
```

Currently, this script includes functionality to:

*   Clean up `__pycache__` directories.
*   Remove `.pyc` and `.tmp` files.

## 5. Troubleshooting

*   **Docker Build Failures**: If you encounter build errors, ensure your `.dockerignore` file is comprehensive to reduce build context size. Check the specific `Dockerfile.<service>` and `requirements-<service>.txt` for the failing service.
*   **Dependency Issues**: "Hash mismatch" or "package not found" errors often indicate incorrect `requirements.txt` usage. Verify that the `Dockerfile` for the service is using the correct service-specific requirements file (e.g., `requirements-communication.txt` for `communication-server`).
*   **Port Conflicts**: Ensure that the ports exposed by the Docker containers (e.g., 3000, 8000-8006, 9000) are not already in use on your host machine.
*   **Container Logs**: Use `docker-compose logs <service_name>` to view the logs of a specific service for debugging.
*   **Health Checks**: If a service isn't starting, check its health check definition in `docker-compose.yml` and try accessing its `/health` endpoint directly if it's exposed.