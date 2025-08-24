"""
Unified Configuration Management System for AI Operating System
Handles centralized configuration for all MCP servers and system components
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for individual MCP servers"""
    enabled: bool = True
    host: str = "localhost"
    port: int = 8000
    timeout: int = 30
    retry_attempts: int = 3
    log_level: str = "INFO"
    max_connections: int = 100
    
    def get_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class GPTOSSConfig:
    """GPT-OSS model configuration"""
    api_key: str = field(default_factory=lambda: os.getenv("HF_TOKEN", ""))
    base_url: str = field(default_factory=lambda: os.getenv("HUGGINGFACE_BASE_URL", "https://api-inference.huggingface.co/models"))
    model_name: str = field(default_factory=lambda: os.getenv("HUGGINGFACE_MODEL_NAME", "microsoft/DialoGPT-large"))
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 30
    fallback_models: List[str] = field(default_factory=lambda: [
        "microsoft/DialoGPT-medium",
        "facebook/blenderbot-400M-distill",
        "EleutherAI/gpt-neo-1.3B"
    ])


@dataclass
class SecurityConfig:
    """Security and permissions configuration"""
    require_auth: bool = False
    jwt_secret: str = ""
    encryption_key: str = ""
    audit_logging: bool = True
    rate_limit: int = 100  # requests per minute
    allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:1420",
        "http://localhost:3000",
        "tauri://localhost"
    ])
    blocked_commands: List[str] = field(default_factory=lambda: [
        "rm -rf /",
        "format",
        "del /q",
        "shutdown",
        "reboot"
    ])


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_enabled: bool = True
    file_path: str = "logs/ai-os.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_files: int = 5
    console_enabled: bool = True
    json_format: bool = True


@dataclass
class FeatureFlags:
    """Feature flags for enabling/disabling system features"""
    voice_recognition: bool = True
    browser_automation: bool = True
    github_integration: bool = True
    whatsapp_integration: bool = True
    email_integration: bool = True
    docker_support: bool = True
    remote_access: bool = False
    experimental_features: bool = False


@dataclass
class UIConfig:
    """UI and frontend configuration"""
    theme: str = "dark"
    language: str = "en"
    auto_start: bool = False
    minimize_to_tray: bool = True
    window_width: int = 1200
    window_height: int = 800
    sidebar_collapsed: bool = false
    notifications_enabled: bool = True


@dataclass
class AIOSConfig:
    """Main configuration class for AI Operating System"""
    version: str = "1.0.0"
    environment: str = "development"
    
    # Server configurations
    servers: Dict[str, ServerConfig] = field(default_factory=lambda: {
        "main": ServerConfig(port=9000),
        "browser": ServerConfig(port=8001),
        "python": ServerConfig(port=8000),
        "system": ServerConfig(port=8002),
        "communication": ServerConfig(port=8003),
        "ide": ServerConfig(port=8004),
        "github": ServerConfig(port=8005),
        "voice_ui": ServerConfig(port=8006),
    })
    
    # GPT-OSS configuration
    gpt_oss: GPTOSSConfig = field(default_factory=GPTOSSConfig)
    
    # Security configuration
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Logging configuration
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Feature flags
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # UI configuration
    ui: UIConfig = field(default_factory=UIConfig)
    
    # API keys and secrets (will be encrypted)
    api_keys: Dict[str, str] = field(default_factory=dict)
    
    # Custom commands and aliases
    custom_commands: Dict[str, str] = field(default_factory=dict)
    
    # MCP tool configurations
    mcp_tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Query stacking settings
    query_stacking: Dict[str, Any] = field(default_factory=lambda: {
        "max_concurrent_queries": 5,
        "timeout_per_step": 300,
        "retry_failed_steps": True,
        "auto_cleanup": True,
        "max_stack_depth": 10
    })


class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or self._get_default_config_dir())
        self.config_file = self.config_dir / "ai-os-config.yaml"
        self.env_file = self.config_dir / ".env"
        self.config = AIOSConfig()
        self._ensure_config_dir()
        self.load()
    
    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory"""
        if os.name == 'nt':  # Windows
            return Path(os.environ.get('APPDATA', '')) / "gpt-oss-ai-os"
        else:  # Unix-like
            return Path.home() / ".config" / "gpt-oss-ai-os"
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        logs_dir = self.config_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
    
    def load(self):
        """Load configuration from file and environment"""
        try:
            # Load from YAML file
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f) or {}
                    self._update_from_dict(yaml_config)
            
            # Load from environment variables
            self._load_from_env()
            
            # Validate configuration
            self.validate()
            
            logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
    
    def save(self):
        """Save configuration to file"""
        try:
            config_dict = asdict(self.config)
            
            # Save as YAML
            with open(self.config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            # Save environment variables
            self._save_env_file()
            
            logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'AI_OS_ENVIRONMENT': 'environment',
            'GPT_OSS_API_KEY': ['gpt_oss', 'api_key'],
            'GPT_OSS_MODEL': ['gpt_oss', 'model_name'],
            'JWT_SECRET': ['security', 'jwt_secret'],
            'ENCRYPTION_KEY': ['security', 'encryption_key'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if isinstance(config_path, list):
                    self._set_nested_value(config_path, value)
                else:
                    setattr(self.config, config_path, value)
    
    def _save_env_file(self):
        """Save environment variables to .env file"""
        env_content = []
        
        # Add sensitive configuration
        if self.config.gpt_oss.api_key:
            env_content.append(f"GPT_OSS_API_KEY={self.config.gpt_oss.api_key}")
        if self.config.security.jwt_secret:
            env_content.append(f"JWT_SECRET={self.config.security.jwt_secret}")
        if self.config.security.encryption_key:
            env_content.append(f"ENCRYPTION_KEY={self.config.security.encryption_key}")
        
        # Add other environment-specific settings
        env_content.append(f"AI_OS_ENVIRONMENT={self.config.environment}")
        
        with open(self.env_file, 'w') as f:
            f.write('\n'.join(env_content))
    
    def _update_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration from dictionary"""
        def update_nested(obj, path, value):
            """Update nested attribute"""
            for key in path[:-1]:
                obj = getattr(obj, key)
            setattr(obj, path[-1], value)
        
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                if isinstance(getattr(self.config, key), dict):
                    # Handle nested configurations
                    for nested_key, nested_value in value.items():
                        nested_attr = getattr(self.config, key)
                        if hasattr(nested_attr, nested_key):
                            setattr(nested_attr, nested_key, nested_value)
                        else:
                            nested_attr[nested_key] = nested_value
                else:
                    setattr(self.config, key, value)
    
    def _set_nested_value(self, path: List[str], value: Any):
        """Set nested configuration value"""
        obj = self.config
        for key in path[:-1]:
            obj = getattr(obj, key)
        setattr(obj, path[-1], value)
    
    def validate(self):
        """Validate configuration values"""
        # Validate ports
        for name, server in self.config.servers.items():
            if not (1 <= server.port <= 65535):
                raise ValueError(f"Invalid port for server {name}: {server.port}")
        
        # Validate GPT-OSS configuration
        if self.config.gpt_oss.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if not (0 <= self.config.gpt_oss.temperature <= 2):
            raise ValueError("temperature must be between 0 and 2")
        
        if not (0 <= self.config.gpt_oss.top_p <= 1):
            raise ValueError("top_p must be between 0 and 1")
        
        # Validate logging level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.config.logging.level}")
    
    def get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """Get configuration for a specific server"""
        return self.config.servers.get(server_name)
    
    def update_server_config(self, server_name: str, config: ServerConfig):
        """Update configuration for a specific server"""
        self.config.servers[server_name] = config
        self.save()
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations as dictionary"""
        return asdict(self.config)
    
    def export_config(self, file_path: str, format: str = 'yaml'):
        """Export configuration to file"""
        config_dict = asdict(self.config)
        
        if format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        else:
            with open(file_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def import_config(self, file_path: str):
        """Import configuration from file"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
        else:
            with open(file_path, 'r') as f:
                config_dict = yaml.safe_load(f)
        
        self._update_from_dict(config_dict)
        self.save()
    
    def create_backup(self) -> str:
        """Create configuration backup"""
        backup_dir = self.config_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"config_backup_{timestamp}.yaml"
        
        self.export_config(str(backup_file))
        
        return str(backup_file)
    
    def restore_backup(self, backup_file: str):
        """Restore configuration from backup"""
        self.import_config(backup_file)
    
    def get_environment_config(self) -> AIOSConfig:
        """Get configuration for current environment"""
        if self.config.environment == 'production':
            # Production-specific overrides
            prod_config = AIOSConfig()
            prod_config.environment = 'production'
            prod_config.logging.level = 'WARNING'
            prod_config.security.require_auth = True
            return prod_config
        
        return self.config


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    
    return _config_manager


def reload_config():
    """Reload configuration from files"""
    global _config_manager
    if _config_manager:
        _config_manager.load()


# Example usage
if __name__ == "__main__":
    # Get configuration manager
    config = get_config_manager()
    
    # Print current configuration
    print("Current configuration:")
    print(json.dumps(config.get_all_configs(), indent=2))
    
    # Update a server configuration
    main_config = config.get_server_config("main")
    if main_config:
        print(f"\nMain server URL: {main_config.get_url()}")
    
    # Create backup
    backup_path = config.create_backup()
    print(f"\nBackup created: {backup_path}")