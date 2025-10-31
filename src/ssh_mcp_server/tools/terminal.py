from typing import Any
from ..ssh_session import SSHSessionManager
from ..tmux_wrapper import TmuxWrapper, TmuxError


def get_terminal_output_tool(session_manager: SSHSessionManager,
                             session_name: str,
                             num_lines: int = 200) -> dict:
    """
    Get current visible terminal output.
    
    MCP Tool: get_terminal_output
    Parameters:
        - session_name: Name of session
        - num_lines: Number of lines to retrieve (default: 200)
    """
    try:
        # 1. Validate session exists
        if not session_manager.state.session_exists(session_name):
            return {
                'success': False,
                'error': f"Session '{session_name}' not found"
            }
        
        # 2. Check tmux session is alive
        if not session_manager.tmux.session_exists(session_name):
            return {
                'success': False,
                'error': f"Session '{session_name}' is not active"
            }
        
        # 3. Capture pane
        output = session_manager.tmux.capture_pane(session_name, num_lines)
        
        # 4. Count actual lines
        lines_count = len(output.split('\n'))
        
        return {
            'success': True,
            'session_name': session_name,
            'output': output,
            'lines': lines_count
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


def interrupt_command_tool(session_manager: SSHSessionManager,
                          session_name: str) -> dict:
    """
    Send Ctrl+C to interrupt running command.
    
    MCP Tool: interrupt_command
    Parameters:
        - session_name: Name of session
    """
    try:
        # 1. Validate session exists
        if not session_manager.state.session_exists(session_name):
            return {
                'success': False,
                'error': f"Session '{session_name}' not found"
            }
        
        # 2. Check tmux session is alive
        if not session_manager.tmux.session_exists(session_name):
            return {
                'success': False,
                'error': f"Session '{session_name}' is not active"
            }
        
        # 3. Send Ctrl+C
        session_manager.tmux.send_ctrl_c(session_name)
        
        return {
            'success': True,
            'session_name': session_name,
            'message': 'Interrupt signal (Ctrl+C) sent'
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




