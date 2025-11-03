from typing import Any
from ..config import ConfigManager, ConfigError


def get_server_info_tool(config_manager: ConfigManager,
                        connection_config_name: str) -> dict:
    """
    Get server-specific information and instructions for a connection configuration.
    
    MCP Tool: get_server_info
    Parameters:
        - connection_config_name: Name of the connection configuration
    Returns:
        - info_content: Content of the info file (if exists)
        - error: Error message (if any)
    """
    try:
        # Get connection config
        conn_config = config_manager.get_connection(connection_config_name)
        if not conn_config:
            available = list(config_manager.connections.keys())
            return {
                'success': False,
                'error': f"Connection config '{connection_config_name}' not found. Available: {available}"
            }
        
        # Check if info_file is configured
        if not conn_config.info_file:
            return {
                'success': False,
                'error': f"Connection config '{connection_config_name}' does not have an info_file configured"
            }
        
        # Read info file
        try:
            with open(conn_config.info_file, 'r', encoding='utf-8') as f:
                info_content = f.read()
            
            return {
                'success': True,
                'connection_config_name': connection_config_name,
                'info_file': conn_config.info_file,
                'info_content': info_content
            }
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Info file not found: {conn_config.info_file}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to read info file '{conn_config.info_file}': {str(e)}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

