# AIOS System Architecture Documentation

This document describes the high-level architecture of the AIOS (AI Orchestration System), outlining its main components, their interactions, and the technologies used.

## 1. Overview

The AIOS is designed to orchestrate and manage AI workloads across a distributed environment. It provides functionalities for command execution, server registration, health monitoring, resource management, and API key management.

## 2. Core Components

### 2.1 Orchestrator Service (`orchestrator_service.py`)

This is the central component of the AIOS. It is responsible for:

*   **API Endpoints:** Exposing RESTful APIs for command execution (`/command`), server registration (`/register_server`), authentication (`/token`), and system operations (`/system/set_resource_limits`, `/system/monitor_resources`).
*   **Load Balancing:** Distributing incoming commands to registered healthy servers using a round-robin strategy.
*   **Server Management:** Maintaining a list of active and healthy servers, including their last known health status and resource utilization.
*   **Health Monitoring:** Periodically checking the health of registered servers via their `/health` endpoint.
*   **API Key Management:** Integrating with the `APIKeyManager` for secure API access.
*   **Caching:** Implementing in-memory caching for frequently accessed data, such as health responses.
*   **Backup System:** Scheduling and managing system backups.

**Key Technologies:**
*   **FastAPI:** For building the asynchronous web API.
*   **Uvicorn:** ASGI server for running the FastAPI application.
*   **Asyncio:** For asynchronous operations, including health checks and command execution.
*   **Redis (Implicit):** Used for session management and potentially other data storage (though not explicitly shown in `orchestrator_service.py`'s direct imports, it's mentioned in context).

### 2.2 API Key Manager (`security/api_key_manager.py`)

Manages the lifecycle of API keys. It provides functionalities for:

*   Generating new API keys.
*   Validating API keys.
*   Revoking and activating API keys.
*   Rotating API keys.
*   Storing API keys in a JSON file (`api_keys.json`).

**Key Technologies:**
*   **`secrets` module:** For generating cryptographically strong random numbers suitable for managing secrets.
*   **`json` module:** For storing API keys persistently.

### 2.3 Authentication Module (`security/auth.py`)

Handles user authentication and authorization using JSON Web Tokens (JWT).

*   **JWT Creation and Validation:** Functions to create and decode JWTs.
*   **Password Hashing:** Securely hashes and verifies user passwords using `bcrypt`.
*   **Dependency Injection:** Integrates with FastAPI's dependency injection system for current user retrieval.

**Key Technologies:**
*   **`jose` library:** For JWT encoding and decoding.
*   **`passlib` library:** For password hashing (bcrypt).
*   **FastAPI's `OAuth2PasswordBearer`:** For OAuth2 token handling.

### 2.4 System Operations Server (`system_operations_server.py`)

(Assumed component based on previous context, not directly provided in current file views)

This component would typically handle system-level operations, such as:

*   Setting resource limits (CPU, memory).
*   Monitoring system resources.
*   Providing system health metrics.

**Key Technologies:**
*   **FastAPI:** For exposing system operation endpoints.
*   **`psutil` (Likely):** For accessing system utilization details.

## 3. Data Flow and Interactions

1.  **Client Request:** A client sends a command execution request to the Orchestrator Service's `/command` endpoint, including an API key or JWT for authentication.
2.  **Authentication/Authorization:** The Orchestrator Service validates the API key (via `APIKeyManager`) or JWT (via `auth.py`).
3.  **Server Selection:** The Orchestrator Service selects a healthy server using its round-robin load balancing strategy.
4.  **Command Forwarding:** The command is forwarded to the selected server.
5.  **Server Response:** The server executes the command and returns the result to the Orchestrator Service.
6.  **Orchestrator Response:** The Orchestrator Service returns the command result to the client.
7.  **Health Checks:** The Orchestrator Service periodically pings the `/health` endpoint of registered servers to update their health status.
8.  **Resource Monitoring:** Clients or internal processes can query the Orchestrator Service or a dedicated System Operations Server for resource utilization metrics.

```mermaid
graph TD
    A[Client] -->|1. Command Request (API Key/JWT)| B(Orchestrator Service)
    B -->|2. Validate API Key/JWT| C{API Key Manager / Auth Module}
    C -->|Validation Result| B
    B -->|3. Select Server (Round Robin)| D[Registered Servers]
    B -->|4. Forward Command| D
    D -->|5. Command Result| B
    B -->|6. Response to Client| A
    B -- periodically -->|7. Health Check| D
    B -- periodically -->|8. Resource Monitoring| D
```

## 4. Deployment Considerations

*   **Containerization:** Deploying components in Docker containers for isolation and portability.
*   **Orchestration:** Using Kubernetes or Docker Swarm for managing and scaling the distributed services.
*   **Monitoring:** Integrating with monitoring tools (e.g., Prometheus, Grafana) for comprehensive system observability.
*   **Logging:** Centralized logging solutions (e.g., ELK stack) for collecting and analyzing logs from all components.
*   **Security:** Implementing network segmentation, firewalls, and regular security audits.

## 5. Future Enhancements

*   **Dynamic Scaling:** Automatically scale servers based on load.
*   **Advanced Load Balancing:** Implement more sophisticated load balancing algorithms (e.g., least connections, weighted round-robin).
*   **Persistent Storage:** Integrate with a robust database solution for persistent storage of system state and configurations.
*   **User Management:** Comprehensive user management system with roles and permissions.
*   **Plugin Architecture:** Allow for easy extension of AIOS functionalities through plugins.