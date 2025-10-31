from typing import Any
from ..config import ConfigManager


def list_available_configs(config_manager: ConfigManager) -> dict:
    """
    List all available SSH server configurations.
    
    MCP Tool: list_available_configs
    Parameters: None
    Returns: List of connection configurations
    """
    try:
        configs = config_manager.list_connections()
        
        return {
            'configs': configs
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'configs': []
        }




