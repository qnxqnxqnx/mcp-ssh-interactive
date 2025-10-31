import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class StateError(Exception):
    """Raised when state operations fail."""
    pass


class SessionState:
    """Represents the state of a single SSH session."""
    
    def __init__(self, session_name: str, connection_config: str, 
                 tmux_session: str, log_file: str, created_at: Optional[str] = None):
        self.session_name = session_name
        self.connection_config = connection_config
        self.tmux_session = tmux_session
        self.log_file = log_file
        self.created_at = created_at or datetime.utcnow().isoformat() + 'Z'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'connection_config': self.connection_config,
            'tmux_session': self.tmux_session,
            'log_file': self.log_file,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, session_name: str, data: dict) -> 'SessionState':
        """Create from dictionary (loaded from JSON)."""
        return cls(
            session_name=session_name,
            connection_config=data['connection_config'],
            tmux_session=data['tmux_session'],
            log_file=data['log_file'],
            created_at=data.get('created_at')
        )


class StateManager:
    """Manages SSH MCP server state (active sessions)."""
    
    STATE_PATH = os.path.expanduser('~/.ssh_mcp_server_state.json')
    VERSION = '1.0'
    
    def __init__(self, state_path: Optional[str] = None):
        self.state_path = state_path or self.STATE_PATH
        self.sessions: Dict[str, SessionState] = {}
        self._load_state()
    
    def _load_state(self):
        """Load state from JSON file."""
        if not os.path.exists(self.state_path):
            # Create empty state file
            self._save_state()
            return
        
        try:
            with open(self.state_path, 'r') as f:
                state_data = json.load(f)
        except json.JSONDecodeError as e:
            raise StateError(f"Failed to parse state file: {e}")
        except Exception as e:
            raise StateError(f"Failed to read state file: {e}")
        
        # Parse sessions
        sessions_data = state_data.get('sessions', {})
        for session_name, session_dict in sessions_data.items():
            self.sessions[session_name] = SessionState.from_dict(session_name, session_dict)
    
    def _save_state(self):
        """Save state to JSON file atomically."""
        state_data = {
            'version': self.VERSION,
            'sessions': {name: session.to_dict() 
                        for name, session in self.sessions.items()}
        }
        
        # Atomic write: write to temp file, then rename
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            
            # Write to temporary file
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(self.state_path),
                prefix='.ssh_mcp_state_',
                suffix='.tmp'
            )
            
            with os.fdopen(fd, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            # Set permissions (600)
            os.chmod(temp_path, 0o600)
            
            # Atomic rename
            os.replace(temp_path, self.state_path)
            
        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise StateError(f"Failed to save state: {e}")
    
    def add_session(self, session_name: str, connection_config: str,
                   tmux_session: str, log_file: str):
        """Add a new session to state."""
        if session_name in self.sessions:
            raise StateError(f"Session '{session_name}' already exists")
        
        session = SessionState(session_name, connection_config, tmux_session, log_file)
        self.sessions[session_name] = session
        self._save_state()
    
    def remove_session(self, session_name: str):
        """Remove a session from state."""
        if session_name in self.sessions:
            del self.sessions[session_name]
            self._save_state()
    
    def get_session(self, session_name: str) -> Optional[SessionState]:
        """Get session by name."""
        return self.sessions.get(session_name)
    
    def session_exists(self, session_name: str) -> bool:
        """Check if session exists in state."""
        return session_name in self.sessions
    
    def list_sessions(self) -> list:
        """Get list of all sessions."""
        return list(self.sessions.values())


# Logging directory utilities

def ensure_log_directory():
    """Create log directory if it doesn't exist."""
    log_dir = os.path.expanduser('~/.ssh_mcp_logs')
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, mode=0o700)
    
    return log_dir


def get_log_file_path(session_name: str) -> str:
    """Get log file path for a session."""
    log_dir = ensure_log_directory()
    return os.path.join(log_dir, f"{session_name}.log")




