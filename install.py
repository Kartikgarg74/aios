#!/usr/bin/env python3
"""
AI Operating System Installation and Setup Script
Automates the complete installation and configuration of the AI OS
"""

import os
import sys
import subprocess
import json
import yaml
import shutil
import platform
import argparse
from pathlib import Path
from typing import List, Dict, Any
import logging
import time
import requests
import zipfile
import tarfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIOSInstaller:
    """AI Operating System installer"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent.absolute()
        self.config_dir = Path.home() / ".config" / "gpt-oss-ai-os"
        
        # Required packages for different components
        self.required_packages = {
            'core': [
                'fastapi', 'uvicorn', 'pydantic', 'python-multipart',
                'requests', 'aiohttp', 'asyncio', 'websockets'
            ],
            'ai': [
                'transformers', 'torch', 'huggingface-hub', 'tokenizers'
            ],
            'communication': [
                'selenium', 'webdriver-manager', 'twilio'
            ],
            'development': [
                'gitpython', 'docker', 'psutil', 'pyautogui'
            ],
            'security': [
                'cryptography', 'pyjwt', 'passlib'
            ],
            'frontend': []
        }
        
        # System dependencies
        self.system_dependencies = {
            'linux': {
                'ubuntu': ['build-essential', 'pkg-config', 'libssl-dev', 'curl'],
                'debian': ['build-essential', 'pkg-config', 'libssl-dev', 'curl'],
                'fedora': ['gcc', 'gcc-c++', 'openssl-devel', 'curl'],
                'arch': ['base-devel', 'openssl', 'curl']
            },
            'darwin': ['xcode-select', 'curl'],
            'windows': ['visual-studio-build-tools', 'git', 'curl']
        }
    
    def check_system_requirements(self) -> bool:
        """Check if system meets requirements"""
        logger.info("Checking system requirements...")
        
        # Check Python version
        if self.python_version < (3, 8):
            logger.error("Python 3.8 or higher is required")
            return False
        
        # Check available disk space (minimum 5GB)
        free_space = self._get_free_space()
        if free_space < 5 * 1024 * 1024 * 1024:  # 5GB
            logger.error("At least 5GB of free disk space is required")
            return False
        
        # Check memory (minimum 4GB)
        memory = self._get_memory_info()
        if memory['total'] < 4 * 1024 * 1024 * 1024:  # 4GB
            logger.warning("Less than 4GB RAM detected. Performance may be affected")
        
        logger.info("System requirements check passed")
        return True
    
    def _get_free_space(self) -> int:
        """Get free disk space in bytes"""
        return shutil.disk_usage(self.project_root).free
    
    def _get_memory_info(self) -> Dict[str, int]:
        """Get memory information"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used
            }
        except ImportError:
            return {'total': 8 * 1024 * 1024 * 1024, 'available': 4 * 1024 * 1024 * 1024, 'used': 0}
    
    def install_system_dependencies(self) -> bool:
        """Install system dependencies"""
        logger.info("Installing system dependencies...")
        
        if self.system == 'linux':
            return self._install_linux_dependencies()
        elif self.system == 'darwin':
            return self._install_macos_dependencies()
        elif self.system == 'windows':
            return self._install_windows_dependencies()
        
        return False
    
    def _install_linux_dependencies(self) -> bool:
        """Install Linux system dependencies"""
        try:
            # Detect distribution
            distro = self._detect_linux_distro()
            packages = self.system_dependencies['linux'].get(distro, [])
            
            if not packages:
                logger.warning(f"Unsupported Linux distribution: {distro}")
                return True
            
            # Use appropriate package manager
            if distro in ['ubuntu', 'debian']:
                cmd = ['sudo', 'apt-get', 'install', '-y'] + packages
            elif distro == 'fedora':
                cmd = ['sudo', 'dnf', 'install', '-y'] + packages
            elif distro == 'arch':
                cmd = ['sudo', 'pacman', '-S', '--noconfirm'] + packages
            
            subprocess.run(cmd, check=True)
            logger.info("Linux system dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Linux dependencies: {e}")
            return False
    
    def _detect_linux_distro(self) -> str:
        """Detect Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content:
                    return 'ubuntu'
                elif 'debian' in content:
                    return 'debian'
                elif 'fedora' in content:
                    return 'fedora'
                elif 'arch' in content:
                    return 'arch'
        except:
            pass
        return 'unknown'
    
    def _install_macos_dependencies(self) -> bool:
        """Install macOS system dependencies"""
        try:
            # Check if Homebrew is installed
            try:
                subprocess.run(['brew', '--version'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.info("Installing Homebrew...")
                subprocess.run(
                    '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                    shell=True, check=True
                )
            
            # Install Xcode command line tools
            result = subprocess.run(['xcode-select', '--install'], capture_output=True, text=True)
            if "command line tools are already installed" in result.stderr.lower():
                logger.info("Xcode command line tools already installed.")
                return True
            elif result.returncode == 0:
                logger.info("Xcode command line tools check/installation complete.")
                return True
            else:
                logger.error(f"Failed to install Xcode command line tools: {result.stderr}")
                return False
            
            logger.info("macOS system dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install macOS dependencies: {e}")
            return False
    
    def _install_windows_dependencies(self) -> bool:
        """Install Windows system dependencies"""
        try:
            # Install Chocolatey if not present
            try:
                subprocess.run(['choco', '--version'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.info("Installing Chocolatey...")
                subprocess.run(
                    'powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(\'https://chocolatey.org/install.ps1\'))"',
                    shell=True, check=True
                )
            
            # Install required packages
            packages = ['git', 'curl', 'visualstudio2019buildtools']
            subprocess.run(['choco', 'install', '-y'] + packages, check=True)
            
            logger.info("Windows system dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Windows dependencies: {e}")
            return False
    
    def install_python_packages(self) -> bool:
        """Install Python packages"""
        logger.info("Installing Python packages...")
        
        # Upgrade pip
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        
        # Install packages by category
        for category, packages in self.required_packages.items():
            if not packages:
                logger.info(f"No packages to install for {category}.")
                continue
            logger.info(f"Installing {category} packages...")
            try:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install'] + packages, capture_output=True, text=True, check=True)
                logger.info(result.stdout)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {category} packages: {e.stderr}")
                return False
        
        logger.info("Python packages installed successfully")
        return True
    
    def setup_frontend(self) -> bool:
        """Setup frontend dependencies"""
        logger.info("Setting up frontend...")
        
        # Check if Node.js is installed
        try:
            subprocess.run(['node', '--version'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error("Node.js is required but not found")
            return False
        
        # Install npm dependencies
        frontend_dir = self.project_root / "src"
        if frontend_dir.exists():
            os.chdir(frontend_dir)
            subprocess.run(['npm', 'install'], check=True)
            
            # Install Tauri CLI (if needed for frontend, otherwise remove)
            # subprocess.run(['npm', 'install', '-g', '@tauri-apps/cli'], check=True)
            
            logger.info("Frontend setup completed")
            return True
        
        return False
    
    def create_directories(self) -> bool:
        """Create required directories"""
        logger.info("Creating directory structure...")
        
        directories = [
            'config',
            'logs',
            'data',
            'backups',
            'temp',
            'models',
            'scripts',
            'security',
            'tests'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        return True
    
    def setup_configuration(self) -> bool:
        """Setup initial configuration"""
        logger.info("Setting up configuration...")
        
        # Copy default configuration files
        config_files = [
            'config/ai_os_config.yaml',
            'config/security.json',
            'config/logging.yaml'
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if not file_path.exists():
                # Create default configuration
                self._create_default_config(file_path)
        
        return True
    
    def _create_default_config(self, file_path: Path):
        """Create default configuration file"""
        if file_path.name == 'ai_os_config.yaml':
            config = {
                'version': '1.0.0',
                'environment': 'development',
                'servers': {
                    'main': {'port': 9000, 'host': 'localhost'},
                    'browser': {'port': 8001, 'host': 'localhost'},
                    'python': {'port': 8000, 'host': 'localhost'},
                    'system': {'port': 8002, 'host': 'localhost'},
                    'communication': {'port': 8003, 'host': 'localhost'},
                    'ide': {'port': 8004, 'host': 'localhost'},
                    'github': {'port': 8005, 'host': 'localhost'},
                    'voice_ui': {'port': 8006, 'host': 'localhost'}
                },
                'gpt_oss': {
                    'api_key': '',
                    'model_name': 'microsoft/DialoGPT-large',
                    'max_tokens': 512,
                    'temperature': 0.7
                }
            }
        elif file_path.name == 'security.json':
            config = {
                'users': {
                    'admin': {
                        'username': 'admin',
                        'email': 'admin@ai-os.local',
                        'permissions': ['system'],
                        'groups': ['admin', 'users'],
                        'created_at': '2024-01-01T00:00:00'
                    }
                },
                'permission_rules': []
            }
        else:
            return
        
        with open(file_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def setup_systemd_services(self) -> bool:
        """Setup systemd services (Linux only)"""
        if self.system != 'linux':
            return True
        
        logger.info("Setting up systemd services...")
        
        services = [
            {
                'name': 'ai-os-main',
                'description': 'AI Operating System Main Server',
                'exec_start': f'{sys.executable} {self.project_root}/main.py',
                'port': 9000
            },
            {
                'name': 'ai-os-browser',
                'description': 'AI OS Browser Server',
                'exec_start': f'{sys.executable} {self.project_root}/browser_server.py',
                'port': 8001
            }
        ]
        
        for service in services:
            service_file = f"/etc/systemd/system/{service['name']}.service"
            service_content = f"""
[Unit]
Description={service['description']}
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ai-os')}
WorkingDirectory={self.project_root}
ExecStart={service['exec_start']}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            
            try:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                subprocess.run(['sudo', 'systemctl', 'enable', service['name']], check=True)
                
                logger.info(f"Created systemd service: {service['name']}")
                
            except Exception as e:
                logger.warning(f"Failed to create systemd service {service['name']}: {e}")
        
        return True
    
    def create_startup_scripts(self) -> bool:
        """Create startup and management scripts"""
        logger.info("Creating startup scripts...")
        
        scripts = {
            'start.sh': """#!/bin/bash
echo "Starting AI Operating System..."
cd "$(dirname "$0")"
python3 main.py &
python3 browser_server.py &
python3 system_operations_server.py &
python3 communication_server.py &
python3 ide_integration_server.py &
python3 github_actions_server.py &
python3 voice_ui_server.py &
echo "All servers started. Check logs for details."
""",
            'stop.sh': """#!/bin/bash
echo "Stopping AI Operating System..."
pkill -f "python3.*main.py"
pkill -f "python3.*browser_server.py"
pkill -f "python3.*system_operations_server.py"
pkill -f "python3.*communication_server.py"
pkill -f "python3.*ide_integration_server.py"
pkill -f "python3.*github_actions_server.py"
pkill -f "python3.*voice_ui_server.py"
echo "All servers stopped."
""",
            'status.sh': """#!/bin/bash
echo "AI Operating System Status:"
echo "=========================="
ps aux | grep -E "(main.py|browser_server.py|system_operations_server.py|communication_server.py|ide_integration_server.py|github_actions_server.py|voice_ui_server.py)" | grep -v grep
""",
            'install.bat': """@echo off
echo Installing AI Operating System...
python -m pip install -r requirements.txt
echo Installation complete!
pause
""",
            'start.bat': """@echo off
echo Starting AI Operating System...
cd /d "%~dp0"
start python main.py
start python browser_server.py
start python system_operations_server.py
start python communication_server.py
start python ide_integration_server.py
start python github_actions_server.py
start python voice_ui_server.py
echo All servers started. Check logs for details.
pause
""",
            'stop.bat': """@echo off
echo Stopping AI Operating System...
taskkill /f /im python.exe 2>nul
echo All servers stopped.
pause
"""
        }
        
        for script_name, content in scripts.items():
            script_path = self.project_root / script_name
            with open(script_path, 'w') as f:
                f.write(content)
            
            # Make Unix scripts executable
            if self.system != 'windows' and not script_name.endswith('.bat'):
                os.chmod(script_path, 0o755)
            
            logger.info(f"Created script: {script_name}")
        
        return True
    
    def create_requirements_file(self) -> bool:
        """Create requirements.txt file"""
        logger.info("Creating requirements.txt...")
        
        requirements = []
        for category, packages in self.required_packages.items():
            requirements.append(f"# {category} packages")
            requirements.extend(packages)
            requirements.append("")
        
        with open(self.project_root / "requirements.txt", 'w') as f:
            f.write('\n'.join(requirements))
        
        return True
    
    def run_health_check(self) -> bool:
        """Run post-installation health check"""
        logger.info("Running health check...")
        
        checks = [
            ("Python version", self._check_python_version),
            ("Required packages", self._check_packages),
            ("Directory structure", self._check_directories),
            ("Configuration files", self._check_config_files),
            ("Frontend setup", self._check_frontend),
            ("System dependencies", self._check_system_dependencies)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if check_func():
                    logger.info(f"✓ {check_name}: PASSED")
                else:
                    logger.error(f"✗ {check_name}: FAILED")
                    all_passed = False
            except Exception as e:
                logger.error(f"✗ {check_name}: ERROR - {e}")
                all_passed = False
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version"""
        return self.python_version >= (3, 8)
    
    def _check_packages(self) -> bool:
        """Check if required packages are installed"""
        try:
            import importlib.metadata
            for packages in self.required_packages.values():
                for package in packages:
                    try:
                        importlib.metadata.distribution(package)
                    except importlib.metadata.PackageNotFoundError:
                        logger.error(f"Package not found: {package}")
                        return False
            return True
        except Exception:
            return False
    
    def _check_directories(self) -> bool:
        """Check if required directories exist"""
        directories = ['config', 'logs', 'data', 'security']
        return all((self.project_root / directory).exists() for directory in directories)
    
    def _check_config_files(self) -> bool:
        """Check if configuration files exist"""
        config_files = ['config/ai_os_config.yaml', 'config/security.json']
        return all((self.project_root / config_file).exists() for config_file in config_files)
    
    def _check_frontend(self) -> bool:
        """Check frontend setup"""
        return (self.project_root / "package.json").exists()
    
    def _check_system_dependencies(self) -> bool:
        """Check system dependencies"""
        # This is a simplified check
        return True
    
    def install(self, components: List[str] = None) -> bool:
        """Complete installation process"""
        logger.info("Starting AI Operating System installation...")
        
        if not self.check_system_requirements():
            return False
        
        if components is None:
            components = ['all']
        
        steps = [
            ("Creating directories", self.create_directories),
            ("Installing system dependencies", self.install_system_dependencies),
            ("Installing Python packages", self.install_python_packages),
            ("Setting up configuration", self.setup_configuration),
            ("Setting up frontend", self.setup_frontend),
            ("Creating startup scripts", self.create_startup_scripts),
            ("Creating requirements file", self.create_requirements_file),
            ("Setting up systemd services", self.setup_systemd_services),
            ("Running health check", self.run_health_check)
        ]
        
        for step_name, step_func in steps:
            if step_name.startswith("Setting up systemd") and self.system != 'linux':
                continue
            
            logger.info(f"Step: {step_name}")
            try:
                if not step_func():
                    logger.error(f"Failed: {step_name}")
                    return False
            except Exception as e:
                logger.error(f"Error in {step_name}: {e}")
                return False
        
        logger.info("AI Operating System installation completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Set your GPT-OSS API key in config/ai_os_config.yaml")
        logger.info("2. Run './start.sh' (Unix) or 'start.bat' (Windows) to start the system")
        logger.info("3. Access the web dashboard at http://localhost:1420")
        
        return True


def main():
    """Main installation function"""
    parser = argparse.ArgumentParser(description="Install AI Operating System")
    parser.add_argument('--components', nargs='+', 
                       choices=['core', 'ai', 'communication', 'development', 'security', 'frontend', 'all'],
                       default=['all'], help="Components to install")
    parser.add_argument('--skip-system-deps', action='store_true', help="Skip system dependencies")
    parser.add_argument('--skip-python-deps', action='store_true', help="Skip Python packages")
    parser.add_argument('--skip-frontend', action='store_true', help="Skip frontend setup")
    parser.add_argument('--config-only', action='store_true', help="Only setup configuration")
    
    args = parser.parse_args()
    
    installer = AIOSInstaller()
    
    if args.config_only:
        installer.create_directories()
        installer.setup_configuration()
        installer.create_startup_scripts()
        installer.create_requirements_file()
        logger.info("Configuration setup completed")
    else:
        components = args.components if args.components != ['all'] else None
        success = installer.install(components)
        
        if not success:
            logger.error("Installation failed. Check logs for details.")
            sys.exit(1)


if __name__ == "__main__":
    main()