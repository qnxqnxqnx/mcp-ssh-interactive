from typing import Any
from ..ssh_session import SSHSessionManager, SSHSessionError


def open_connection_tool(session_manager: SSHSessionManager, 
                        connection_config_name: str,
                        session_name: str) -> dict:
    """
    Open a new SSH connection.
    
    MCP Tool: open_connection
    Parameters:
        - connection_config_name: Name from config file
        - session_name: Unique name for this session
    """
    try:
        result = session_manager.open_connection(connection_config_name, session_name)
        return result
        
    except SSHSessionError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {e}'
        }


def close_connection_tool(session_manager: SSHSessionManager,
                         session_name: str) -> dict:
    """
    Close an SSH connection.
    
    MCP Tool: close_connection
    Parameters:
        - session_name: Name of session to close
    """
    try:
        result = session_manager.close_connection(session_name)
        return result
        
    except SSHSessionError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {e}'
        }


def list_connections_tool(session_manager: SSHSessionManager) -> dict:
    """
    List all active SSH sessions.
    
    MCP Tool: list_connections
    Parameters: None
    """
    try:
        result = session_manager.list_connections()
        return result
        
    except Exception as e:
        return {
            'sessions': [],
            'total': 0,
            'error': str(e)
        }




