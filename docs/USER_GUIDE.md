# AIOS User Guide

## Introduction

The AI Operating System (AIOS) is a comprehensive AI-powered environment that integrates multiple MCP (Model Context Protocol) servers to provide intelligent automation, system management, and user interaction capabilities. This guide will help you get started with AIOS and explore its features.

## System Requirements

- Python 3.8 or higher
- Node.js 16+ and npm
- Git
- 5GB free disk space
- 4GB RAM (8GB recommended)

## Installation

### Quick Install

```bash
# Clone the repository
git clone <repository-url>
cd aios_2gb

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

# Set your API key
gpt_oss:
  api_key: "your-api-key"
  model_name: "microsoft/DialoGPT-large"
```

## Getting Started

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
# Start the main orchestrator
python main.py

# Start individual servers in separate terminals
python browser_server.py
python system_server.py
python communication_server.py
python ide_server.py
python github_server.py
python voice_ui_server.py
```

### Accessing the Dashboard

Once the system is running, you can access the dashboard at:

- **Web Interface**: http://localhost:9000
- **Desktop App**: The Tauri app should launch automatically

## Core Features

### Command Input

You can interact with AIOS using natural language commands through:

1. **Command Line Interface**: Type commands in the terminal
2. **Web Dashboard**: Use the CommandInput component
3. **Voice Commands**: Speak commands if voice recognition is enabled

### Available Commands

#### System Operations
- "Open application [name]"
- "Create file [filename]"
- "List files in [directory]"
- "Show system status"
- "Run [command] in terminal"

#### Browser Automation
- "Search web for [query]"
- "Open website [url]"
- "Download file from [url]"

#### Communication
- "Send email to [contact]"
- "Send WhatsApp message to [contact]"
- "Make call to [contact]"

#### Development
- "Open VS Code for [project]"
- "Run tests for [project]"
- "Create pull request for [repository]"

### AI Chat Interface

The AI Chat interface allows for conversational interaction with the system. You can:

1. Ask questions about system status
2. Request complex multi-step operations
3. Get help with troubleshooting

### Settings and Configuration

Access settings through the dashboard to configure:

- API keys and authentication
- Theme preferences
- Feature toggles
- Server configurations

## Troubleshooting

### Common Issues

#### Server Connection Problems

**Symptom**: Cannot connect to one or more servers

**Solution**:
1. Check if the server is running: `ps aux | grep server_name`
2. Verify port availability: `netstat -tuln | grep port_number`
3. Restart the specific server

#### API Key Issues

**Symptom**: Authentication errors or API key rejected

**Solution**:
1. Verify API key in configuration
2. Check API key expiration
3. Generate a new key if necessary

#### Performance Problems

**Symptom**: Slow response times or high resource usage

**Solution**:
1. Check system resources: `htop` or Task Manager
2. Adjust resource limits in configuration
3. Close unnecessary applications

### Getting Help

If you encounter issues not covered in this guide:

1. Check the logs in the `logs/` directory
2. Consult the troubleshooting guide
3. Submit an issue with detailed information

## Advanced Usage

### Custom Commands

You can create custom commands and aliases in the configuration:

```yaml
custom_commands:
  backup_projects: "SystemOps.copy_files(source='./projects', destination='./backups')"
  update_repos: "IDEIntegration.pull_all_repos()"
```

### Automation Workflows

Create complex automation workflows by chaining commands:

```
"Backup important files and clean temp directory"
    ├── Step 1: SystemOps.create_directory(path="./backups")
    ├── Step 2: SystemOps.copy_files(source="./important", destination="./backups")
    ├── Step 3: SystemOps.clean_temp_files()
    └── Step 4: SystemOps.get_disk_usage()
```

### Resource Management

Monitor and manage system resources:

- Memory usage: `ps aux | grep python`
- Adjust server limits in configuration
- Use process pools for heavy operations

## Security Best Practices

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

## Backup and Recovery

### Configuration Backup
```bash
# Create backup
python -c "from config.ai_os_config import get_config_manager; get_config_manager().create_backup()"

# Restore from backup
python -c "from config.ai_os_config import get_config_manager; get_config_manager().restore_backup('backup_file.yaml')"
```

### Data Backup
```bash
# Backup all data
tar -czf backup-$(date +%Y%m%d).tar.gz config/ logs/ data/

# Restore data
tar -xzf backup-20240101.tar.gz
```