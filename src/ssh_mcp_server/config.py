import os
import yaml
from typing import Dict, Optional
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConnectionConfig:
    """Represents a single SSH connection configuration."""
    
    def __init__(self, name: str, config_dict: dict):
        self.name = name
        self.host = config_dict.get('host')
        self.user = config_dict.get('user')
        self.key_path = config_dict.get('key_path')
        self.port = config_dict.get('port', 22)
        self.password = config_dict.get('password')  # Optional
        self.description = config_dict.get('description', '')
        
        # Validate required fields
        if not self.host:
            raise ConfigError(f"Connection '{name}': 'host' is required")
        if not self.user:
            raise ConfigError(f"Connection '{name}': 'user' is required")
        if not self.key_path:
            raise ConfigError(f"Connection '{name}': 'key_path' is required")
        
        # Expand path
        self.key_path = os.path.expanduser(self.key_path)
        
        # Verify key file exists
        if not os.path.exists(self.key_path):
            raise ConfigError(f"Connection '{name}': Key file not found: {self.key_path}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses, without sensitive data)."""
        return {
            'name': self.name,
            'host': self.host,
            'user': self.user,
            'port': self.port,
            'description': self.description
        }


class ConfigManager:
    """Manages SSH MCP server configuration."""
    
    CONFIG_PATH = os.path.expanduser('~/.ssh_mcp_config.yml')
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.CONFIG_PATH
        self.connections: Dict[str, ConnectionConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """Load and parse configuration file."""
        if not os.path.exists(self.config_path):
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read config file: {e}")
        
        if not config_data:
            raise ConfigError("Configuration file is empty")
        
        if 'connections' not in config_data:
            raise ConfigError("Configuration must contain 'connections' section")
        
        connections_data = config_data['connections']
        if not isinstance(connections_data, dict):
            raise ConfigError("'connections' must be a dictionary")
        
        # Parse each connection
        for name, conn_config in connections_data.items():
            try:
                self.connections[name] = ConnectionConfig(name, conn_config)
            except ConfigError as e:
                raise ConfigError(f"Invalid connection config '{name}': {e}")
    
    def get_connection(self, name: str) -> Optional[ConnectionConfig]:
        """Get connection configuration by name."""
        return self.connections.get(name)
    
    def list_connections(self) -> list:
        """Get list of all connection configurations."""
        return [conn.to_dict() for conn in self.connections.values()]
    
    def connection_exists(self, name: str) -> bool:
        """Check if connection configuration exists."""
        return name in self.connections




