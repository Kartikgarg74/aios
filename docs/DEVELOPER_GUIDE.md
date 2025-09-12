# AIOS Developer Documentation

## Architecture Overview

The AIOS (AI Operating System) uses a modular architecture with multiple MCP (Model Context Protocol) servers working together to provide an AI-powered environment.

### Core Components

#### 1. Orchestrator Service

Central component responsible for API endpoints, load balancing, server management, health monitoring, and API key management.

**Technologies**: FastAPI, Uvicorn, Asyncio, Redis

#### 2. MCP Servers

- **Main Server (Port 9000)**: Central orchestrator and API gateway
- **Browser Server (Port 8001)**: Web automation and browser control
- **Python Server (Port 8000)**: Python code execution and analysis
- **System Operations Server (Port 8002)**: File system and process management
- **Communication Server (Port 8003)**: WhatsApp, email, and phone integration
- **IDE Integration Server (Port 8004)**: VS Code and development tools
- **GitHub Actions Server (Port 8005)**: Repository management and CI/CD
- **Voice/UI Server (Port 8006)**: Speech recognition and GUI automation

#### 3. Security Layer

- **API Key Manager**: Manages API key lifecycle
- **Authentication Module**: Handles JWT-based authentication

#### 4. Frontend

- **Tauri Desktop App**: Native desktop application
- **React Dashboard**: Web-based monitoring and control interface

## API Interfaces

### Orchestrator Service API

- **POST /token**: Generates JWT token for authentication
- **POST /register_server**: Registers a new MCP server
- **POST /command**: Executes a command on appropriate server
- **GET /system/status**: Returns system status information

### Browser Server API (Port 8001)

- **POST /search**: Performs web search
- **POST /open_url**: Opens URL in browser

### System Operations Server API (Port 8002)

- **POST /execute_command**: Executes system command
- **POST /launch_application**: Launches desktop application

### Communication Server API (Port 8003)

- **POST /send_email**: Sends email
- **POST /send_whatsapp**: Sends WhatsApp message

### IDE Integration Server API (Port 8004)

- **POST /open_vscode**: Opens VS Code
- **POST /git_command**: Executes git command

### GitHub Actions Server API (Port 8005)

- **POST /clone_repository**: Clones GitHub repository
- **POST /create_pull_request**: Creates pull request

### Voice/UI Server API (Port 8006)

- **POST /start_voice_recognition**: Starts voice recognition
- **POST /execute_voice_command**: Executes voice command

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Node.js 16+ and npm
- Git
- Docker (optional, for containerized development)

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aios_2gb
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Setup frontend development**
   ```bash
   cd frontend/web
   npm install
   ```

### Development Workflow

#### Running in Development Mode

```bash
# Start the orchestrator with hot reload
uvicorn orchestrator_service:app --reload --port 9000

# Start individual servers with hot reload
uvicorn browser_server:app --reload --port 8001
```

#### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

## Extending AIOS

### Creating a New MCP Server

1. **Create a new server file**
   ```python
   # custom_server.py
   from fastapi import FastAPI
   from fastmcp import FastMCP
   
   app = FastAPI()
   mcp = FastMCP(name="custom_server")
   app.mount("/mcp", mcp)
   
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   
   # Add your custom endpoints
   @app.post("/custom_endpoint")
   async def custom_endpoint(data: dict):
       # Implementation
       return {"result": "success"}
   ```

2. **Register with the orchestrator**
   ```python
   import requests
   
   requests.post("http://localhost:9000/register_server", json={
       "name": "custom_server",
       "url": "http://localhost:8007",  # Choose an available port
       "type": "custom"
   })
   ```

## Code Style and Guidelines

- Follow PEP 8 guidelines for Python
- Use type hints for function parameters and return values
- Document classes and functions with docstrings
- Follow ESLint configuration for JavaScript/TypeScript
- Write unit tests for all new functionality

## Contribution Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Future Development

- **Dynamic Scaling**: Automatically scale servers based on load
- **Advanced Load Balancing**: Implement more sophisticated load balancing algorithms
- **Persistent Storage**: Integrate with robust database solution
- **User Management**: Comprehensive user management system with roles and permissions
- **Plugin Architecture**: Allow for easy extension of AIOS functionalities through plugins