from typing import Any
from ..ssh_session import SSHSessionManager
from ..tmux_wrapper import TmuxWrapper, TmuxError


def execute_command_tool(session_manager: SSHSessionManager,
                        session_name: str,
                        command: str) -> dict:
    """
    Execute a command on the remote server.
    
    MCP Tool: execute_command
    Parameters:
        - session_name: Name of session
        - command: Command to execute
    Returns: success status
    """
    try:
        # 1. Validate session exists
        if not session_manager.state.session_exists(session_name):
            available = [s.session_name for s in session_manager.state.list_sessions()]
            return {
                'success': False,
                'error': f"Session '{session_name}' not found. Available: {available}"
            }
        
        # 2. Check tmux session is alive
        if not session_manager.tmux.session_exists(session_name):
            return {
                'success': False,
                'error': f"Session '{session_name}' is not active (tmux session not found)"
            }
        
        # 3. Send command
        session_manager.tmux.send_command(session_name, command)
        
        # 4. Return immediately
        return {
            'success': True,
            'session_name': session_name,
            'command': command,
            'message': 'Command sent'
        }
        
    except TmuxError as e:
        return {
            'success': False,
            'error': f'Tmux error: {e}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {e}'
        }




