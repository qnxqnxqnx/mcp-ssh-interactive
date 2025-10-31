import time
import os
from typing import Optional
from .tmux_wrapper import TmuxWrapper, TmuxError
from .config import ConfigManager, ConnectionConfig
from .state import StateManager, ensure_log_directory, get_log_file_path


class SSHSessionError(Exception):
    """Raised when SSH session operations fail."""
    pass


class SSHSessionManager:
    """Manages SSH connections and sessions."""
    
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config = config_manager
        self.state = state_manager
        self.tmux = TmuxWrapper()
    
    def open_connection(self, connection_config_name: str, session_name: str) -> dict:
        """
        Open a new SSH connection.
        
        Returns dict with connection info.
        Raises SSHSessionError on failure.
        """
        # 1. Validate connection config exists
        conn_config = self.config.get_connection(connection_config_name)
        if not conn_config:
            available = list(self.config.connections.keys())
            raise SSHSessionError(
                f"Connection config '{connection_config_name}' not found. "
                f"Available: {available}"
            )
        
        # 2. Validate session name format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_name):
            raise SSHSessionError(
                f"Invalid session name '{session_name}'. "
                "Must contain only alphanumeric characters, underscores, and hyphens."
            )
        
        # 3. Check session name not already in use
        if self.state.session_exists(session_name):
            raise SSHSessionError(f"Session name '{session_name}' already exists")
        
        # 4. Create log directory
        ensure_log_directory()
        log_file = get_log_file_path(session_name)
        
        # 5. Create tmux session
        try:
            self.tmux.create_session(session_name)
        except TmuxError as e:
            raise SSHSessionError(f"Failed to create tmux session: {e}")
        
        # 6. Set history limit
        try:
            self.tmux.set_history_limit(session_name, 200000)
        except TmuxError as e:
            self.tmux.kill_session(session_name)
            raise SSHSessionError(f"Failed to set history limit: {e}")
        
        # 7. Start SSH connection
        ssh_command = self._build_ssh_command(conn_config)
        try:
            self.tmux.send_command(session_name, ssh_command)
        except TmuxError as e:
            self.tmux.kill_session(session_name)
            raise SSHSessionError(f"Failed to start SSH: {e}")
        
        # 8. Start logging
        try:
            self.tmux.start_logging(session_name, log_file)
        except TmuxError as e:
            self.tmux.kill_session(session_name)
            raise SSHSessionError(f"Failed to start logging: {e}")
        
        # 9. Wait for connection to establish
        time.sleep(3)
        
        # 10. Check connection success
        try:
            output = self.tmux.capture_pane(session_name, num_lines=50)
            
            # Look for connection errors
            error_patterns = [
                'connection refused',
                'permission denied',
                'host key verification failed',
                'no route to host',
                'network is unreachable'
            ]
            
            output_lower = output.lower()
            for pattern in error_patterns:
                if pattern in output_lower:
                    self.tmux.kill_session(session_name)
                    raise SSHSessionError(f"SSH connection failed: {pattern}")
            
        except TmuxError as e:
            self.tmux.kill_session(session_name)
            raise SSHSessionError(f"Failed to verify connection: {e}")
        
        # 11. Update state file
        try:
            self.state.add_session(
                session_name=session_name,
                connection_config=connection_config_name,
                tmux_session=session_name,
                log_file=log_file
            )
        except Exception as e:
            self.tmux.kill_session(session_name)
            raise SSHSessionError(f"Failed to update state: {e}")
        
        # 12. Return success
        return {
            'success': True,
            'session_name': session_name,
            'message': 'SSH connection established',
            'connection_info': {
                'host': conn_config.host,
                'user': conn_config.user,
                'port': conn_config.port
            }
        }
    
    def close_connection(self, session_name: str) -> dict:
        """Close an SSH connection."""
        # 1. Validate session exists
        if not self.state.session_exists(session_name):
            available = [s.session_name for s in self.state.list_sessions()]
            raise SSHSessionError(
                f"Session '{session_name}' not found. Available: {available}"
            )
        
        # 2. Kill tmux session (ignore errors if already dead)
        try:
            self.tmux.kill_session(session_name)
        except TmuxError:
            pass  # Session might already be dead
        
        # 3. Remove from state
        self.state.remove_session(session_name)
        
        return {
            'success': True,
            'session_name': session_name,
            'message': 'Connection closed successfully'
        }
    
    def list_connections(self) -> dict:
        """List all active connections."""
        sessions = []
        
        for session_state in self.state.list_sessions():
            # Get connection config info
            conn_config = self.config.get_connection(session_state.connection_config)
            
            # Check if tmux session is alive
            status = 'active' if self.tmux.session_exists(session_state.session_name) else 'disconnected'
            
            session_info = {
                'session_name': session_state.session_name,
                'connection_config': session_state.connection_config,
                'status': status
            }
            
            if conn_config:
                session_info['host'] = conn_config.host
                session_info['user'] = conn_config.user
            
            sessions.append(session_info)
        
        return {
            'sessions': sessions,
            'total': len(sessions)
        }
    
    def _build_ssh_command(self, conn_config: ConnectionConfig) -> str:
        """Build SSH command string."""
        # Use -tt for pseudo-terminal (interactive behavior)
        cmd_parts = [
            'ssh',
            '-tt',
        ]
        
        # Add key path if provided (recommended for security)
        if conn_config.key_path:
            cmd_parts.extend(['-i', conn_config.key_path])
        
        if conn_config.port != 22:
            cmd_parts.extend(['-p', str(conn_config.port)])
        
        cmd_parts.append(f'{conn_config.user}@{conn_config.host}')
        
        return ' '.join(cmd_parts)
    
    def get_session_status(self, session_name: str) -> str:
        """Get status of a session (active/disconnected)."""
        if not self.state.session_exists(session_name):
            return 'not_found'
        
        return 'active' if self.tmux.session_exists(session_name) else 'disconnected'




