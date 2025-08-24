# AI Operating System Documentation

## Overview

The AI Operating System (AIOS) is a comprehensive AI-powered desktop environment that integrates multiple MCP (Model Context Protocol) servers to provide intelligent automation, system management, and user interaction capabilities. Built with a modular architecture, it combines local processing with cloud-based AI services to deliver a unified, intelligent computing experience.

## Architecture

### System Components

#### 1. Core MCP Servers
- **Main Server (Port 9000)**: Central orchestrator and API gateway
- **Browser Server (Port 8001)**: Web automation and browser control
- **Python Server (Port 8000)**: Python code execution and analysis
- **System Operations Server (Port 8002)**: File system and process management
- **Communication Server (Port 8003)**: WhatsApp, email, and phone integration
- **IDE Integration Server (Port 8004)**: VS Code and development tools
- **GitHub Actions Server (Port 8005)**: Repository management and CI/CD
- **Voice/UI Server (Port 8006)**: Speech recognition and GUI automation

#### 2. AI Integration
- **GPT-OSS Model**: Uses Hugging Face API for intelligent decision-making
- **Query Stacking**: Complex multi-step operation management
- **Context Awareness**: Maintains session state and user preferences

#### 3. Frontend
- **Tauri Desktop App**: Native desktop application with web technologies
- **React Dashboard**: Web-based monitoring and control interface
- **System Tray Integration**: Background operation with quick access

#### 4. Security Layer
- **Permission Management**: Role-based access control
- **Audit Logging**: Comprehensive security event tracking
- **Encryption**: Sensitive data protection
- **JWT Authentication**: Secure API access

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 16+ and npm
- Git
- 5GB free disk space
- 4GB RAM (8GB recommended)

### Quick Install
```bash
# Clone the repository
git clone <repository-url>
cd gpt-oss-mcp-server

# Run the installer
python install.py

# Or for specific components
python install.py --components core ai frontend
```

### Manual Installation

#### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Install System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install build-essential pkg-config libssl-dev curl

# macOS
xcode-select --install
brew install curl

# Windows (with Chocolatey)
choco install visualstudio2019buildtools git curl
```

#### 3. Setup Frontend
```bash
cd src-tauri
npm install
npm install -g @tauri-apps/cli
```

#### 4. Configuration
```bash
# Edit configuration
nano config/ai_os_config.yaml

# Set your GPT-OSS API key
gpt_oss:
  api_key: "your-huggingface-api-key"
  model_name: "microsoft/DialoGPT-large"
```

## Usage

### Starting the System

#### Method 1: Using Scripts
```bash
# Unix/Linux/macOS
./start.sh

# Windows
start.bat
```

#### Method 2: Manual Start
```bash
# Start each server individually
python main.py &
python browser_server.py &
python system_operations_server.py &
python communication_server.py &
python ide_integration_server.py &
python github_actions_server.py &
python voice_ui_server.py &
```

### Accessing the Interface

#### Desktop Application
```bash
cd src-tauri
tauri dev
```

#### Web Dashboard
Open browser to: `http://localhost:1420`

### Basic Operations

#### 1. File Management
```python
# Via API
import requests

# List files
response = requests.get('http://localhost:8002/list_directory', json={'path': '/home/user'})

# Create file
response = requests.post('http://localhost:8002/create_file', json={'path': '/tmp/test.txt', 'content': 'Hello AIOS'})
```

#### 2. Communication
```python
# Send email
response = requests.post('http://localhost:8003/send_email', json={
    'to': 'recipient@example.com',
    'subject': 'Test from AIOS',
    'body': 'Hello from AI Operating System!'
})

# Send WhatsApp message
response = requests.post('http://localhost:8003/send_whatsapp', json={
    'to': '+1234567890',
    'message': 'Hello from AIOS!'
})
```

#### 3. Development Operations
```python
# Open VS Code
response = requests.post('http://localhost:8004/open_vscode', json={'path': '/path/to/project'})

# Git operations
response = requests.post('http://localhost:8004/git_command', json={
    'repo_path': '/path/to/repo',
    'command': 'status'
})
```

#### 4. GitHub Integration
```python
# Clone repository
response = requests.post('http://localhost:8005/clone_repository', json={
    'url': 'https://github.com/user/repo.git',
    'local_path': '/path/to/clone'
})

# Create pull request
response = requests.post('http://localhost:8005/create_pull_request', json={
    'repo_path': '/path/to/repo',
    'title': 'New feature',
    'body': 'Description of changes'
})
```

### Voice Commands

#### Available Commands
- "Open application [name]"
- "Create file [filename]"
- "Search web for [query]"
- "Send email to [contact]"
- "Run terminal command [command]"
- "Save my work"

#### Voice Setup
```bash
# Enable voice recognition
python voice_ui_server.py --enable-voice

# Test voice commands
curl -X POST http://localhost:8006/execute_voice_command -d '{"command": "open application firefox"}'
```

## Configuration

### Main Configuration (`config/ai_os_config.yaml`)

```yaml
version: "1.0.0"
environment: "development"

servers:
  main:
    port: 9000
    host: "localhost"
  browser:
    port: 8001
    host: "localhost"
  # ... other servers

gpt_oss:
  api_key: "your-api-key"
  model_name: "microsoft/DialoGPT-large"
  max_tokens: 512
  temperature: 0.7

security:
  require_auth: false
  jwt_secret: "your-secret-key"
  audit_logging: true

features:
  voice_recognition: true
  browser_automation: true
  github_integration: true
  whatsapp_integration: true
```

### Security Configuration

#### User Management
```python
from security.security_manager import get_security_manager

security = get_security_manager()

# Add user
user_id = security.add_user(
    username="john",
    email="john@example.com",
    permissions=["read", "write", "execute"],
    groups=["users", "developers"]
)

# Check permissions
has_permission = security.check_permission(user_id, "file/home", "write")
```

#### Audit Logs
```python
# Get security events
events = security.get_audit_log(
    start_time=datetime.now() - timedelta(days=7),
    event_types=[SecurityEventType.AUTH_FAILURE, SecurityEventType.PERMISSION_DENIED]
)
```

## Query Stacking System

### Creating Complex Operations

```python
# Create a query stack
from gpt_oss_integration import QueryStackingSystem

stacking = QueryStackingSystem()

# Define multi-step operation
query = {
    "name": "Deploy Project",
    "steps": [
        {
            "tool": "github",
            "action": "clone_repository",
            "params": {"url": "https://github.com/user/project.git"}
        },
        {
            "tool": "ide",
            "action": "open_vscode",
            "params": {"path": "/path/to/project"}
        },
        {
            "tool": "system",
            "action": "execute_command",
            "params": {"command": "npm install"}
        },
        {
            "tool": "github",
            "action": "create_pull_request",
            "params": {"title": "Deployment ready"}
        }
    ]
}

# Execute the stack
stack_id = stacking.create_stack(query)
result = stacking.execute_stack(stack_id)
```

### Monitoring Query Progress

```python
# Check stack status
status = stacking.get_stack_status(stack_id)
print(f"Status: {status['status']}")
print(f"Current step: {status['current_step']}")
print(f"Progress: {status['progress']}%")
```

## API Reference

### System Operations Server (Port 8002)

#### Endpoints

**GET /list_directory**
- Lists files and directories
- Parameters: `{"path": "/path/to/directory"}`

**POST /create_file**
- Creates a new file
- Parameters: `{"path": "/path/to/file", "content": "file content"}`

**POST /execute_command**
- Executes system command
- Parameters: `{"command": "ls -la", "working_dir": "/path"}`

**POST /launch_application**
- Launches desktop application
- Parameters: `{"app_name": "firefox", "args": ["--new-tab"]}`

### Communication Server (Port 8003)

#### Endpoints

**POST /send_email**
- Sends email
- Parameters: `{"to": "user@example.com", "subject": "Subject", "body": "Content"}`

**POST /send_whatsapp**
- Sends WhatsApp message
- Parameters: `{"to": "+1234567890", "message": "Hello"}`

**POST /make_call**
- Makes phone call
- Parameters: `{"to": "+1234567890", "message": "Automated call"}`

### IDE Integration Server (Port 8004)

#### Endpoints

**POST /open_vscode**
- Opens VS Code
- Parameters: `{"path": "/project/path"}`

**POST /git_command**
- Executes git command
- Parameters: `{"repo_path": "/repo/path", "command": "status"}`

**POST /run_tests**
- Runs project tests
- Parameters: `{"project_path": "/project/path", "test_command": "pytest"}`

### GitHub Actions Server (Port 8005)

#### Endpoints

**POST /clone_repository**
- Clones GitHub repository
- Parameters: `{"url": "https://github.com/user/repo.git", "local_path": "/path"}`

**POST /create_workflow**
- Creates GitHub Actions workflow
- Parameters: `{"repo_path": "/repo/path", "workflow_name": "CI", "config": {...}}`

**POST /create_pull_request**
- Creates pull request
- Parameters: `{"repo_path": "/repo/path", "title": "PR Title", "body": "Description"}`

### Voice/UI Server (Port 8006)

#### Endpoints

**POST /start_voice_recognition**
- Starts voice recognition
- Parameters: `{"language": "en-US", "continuous": true}`

**POST /text_to_speech**
- Converts text to speech
- Parameters: `{"text": "Hello world", "voice": "default"}`

**POST /execute_voice_command**
- Executes voice command
- Parameters: `{"command": "open application firefox"}`

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 2. Permission Denied
```bash
# Fix permissions
chmod +x start.sh
chmod +x stop.sh
```

#### 3. Missing Dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

#### 4. Frontend Build Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall frontend dependencies
cd src-tauri
rm -rf node_modules package-lock.json
npm install
```

### Debug Mode

Enable debug logging:
```bash
export AI_OS_LOG_LEVEL=DEBUG
python main.py --debug
```

### Log Files

- Application logs: `logs/ai-os.log`
- Security logs: `logs/security-audit.log`
- Server logs: `logs/server-{port}.log`

## Development

### Adding New MCP Servers

1. Create server file:
```python
# new_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8007)
```

2. Register in configuration:
```yaml
servers:
  new_server:
    port: 8007
    host: "localhost"
```

3. Add to startup scripts

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

### Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_security.py

# Run with coverage
python -m pytest --cov=src tests/
```

## Performance Optimization

### Resource Management

#### Memory Usage
- Monitor with: `ps aux | grep python`
- Adjust server limits in configuration
- Use process pools for heavy operations

#### CPU Usage
- Limit concurrent operations
- Use async/await patterns
- Monitor with system tools

#### Network Optimization
- Enable compression
- Use connection pooling
- Cache API responses

### Scaling

#### Horizontal Scaling
- Run servers on different machines
- Use load balancers
- Implement service discovery

#### Vertical Scaling
- Increase server resources
- Optimize code performance
- Use faster hardware

## Security Best Practices

### Production Deployment

1. **Enable Authentication**
   ```yaml
   security:
     require_auth: true
     jwt_secret: "strong-secret-key"
   ```

2. **Use HTTPS**
   - Configure SSL certificates
   - Use reverse proxy (nginx)
   - Enable HSTS

3. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Apply patches promptly

4. **Access Control**
   - Limit network access
   - Use firewall rules
   - Monitor audit logs

### Backup and Recovery

#### Configuration Backup
```bash
# Create backup
python -c "from config.ai_os_config import get_config_manager; get_config_manager().create_backup()"

# Restore from backup
python -c "from config.ai_os_config import get_config_manager; get_config_manager().restore_backup('backup_file.yaml')"
```

#### Data Backup
```bash
# Backup all data
tar -czf backup-$(date +%Y%m%d).tar.gz config/ logs/ data/

# Restore data
tar -xzf backup-20240101.tar.gz
```

## Support

### Getting Help

1. **Documentation**: This file and inline code comments
2. **Issues**: Create GitHub issue with detailed description
3. **Discussions**: Use GitHub Discussions for questions
4. **Community**: Join our Discord/Slack community

### Reporting Issues

Include in bug reports:
- System information (OS, Python version)
- Steps to reproduce
- Error messages and logs
- Configuration files (sanitized)

### Feature Requests

Submit feature requests via:
- GitHub Issues with "enhancement" label
- Detailed use case description
- Proposed implementation approach

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- Hugging Face for GPT-OSS model integration
- Tauri team for desktop framework
- FastAPI team for web framework
- All contributors and community members

---

For more detailed information, refer to the inline code documentation and specific server documentation files.