import subprocess
import time
from typing import Optional, Tuple


class TmuxError(Exception):
    """Raised when tmux operations fail."""
    pass


class TmuxWrapper:
    """Wrapper for tmux command operations."""
    
    @staticmethod
    def check_tmux_installed() -> bool:
        """Check if tmux is installed and accessible."""
        try:
            result = subprocess.run(
                ['tmux', '-V'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def session_exists(session_name: str) -> bool:
        """Check if a tmux session exists."""
        try:
            result = subprocess.run(
                ['tmux', 'has-session', '-t', session_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout checking session '{session_name}'")
    
    @staticmethod
    def create_session(session_name: str) -> bool:
        """Create a new detached tmux session."""
        try:
            result = subprocess.run(
                ['tmux', 'new-session', '-d', '-s', session_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise TmuxError(f"Failed to create session: {result.stderr}")
            
            return True
            
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout creating session '{session_name}'")
    
    @staticmethod
    def set_history_limit(session_name: str, limit: int = 200000):
        """Set history limit for a tmux session."""
        try:
            result = subprocess.run(
                ['tmux', 'set-option', '-t', session_name, 
                 'history-limit', str(limit)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise TmuxError(f"Failed to set history limit: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout setting history limit for '{session_name}'")
    
    @staticmethod
    def send_keys(session_name: str, keys: str, literal: bool = False):
        """Send keys to a tmux session."""
        try:
            cmd = ['tmux', 'send-keys', '-t', session_name]
            
            if literal:
                cmd.append('-l')
            
            cmd.append(keys)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise TmuxError(f"Failed to send keys: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout sending keys to '{session_name}'")
    
    @staticmethod
    def send_command(session_name: str, command: str):
        """Send a command (with Enter) to a tmux session."""
        TmuxWrapper.send_keys(session_name, command)
        TmuxWrapper.send_keys(session_name, 'Enter')
    
    @staticmethod
    def send_ctrl_c(session_name: str):
        """Send Ctrl+C to a tmux session."""
        try:
            result = subprocess.run(
                ['tmux', 'send-keys', '-t', session_name, 'C-c'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise TmuxError(f"Failed to send Ctrl+C: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout sending Ctrl+C to '{session_name}'")
    
    @staticmethod
    def start_logging(session_name: str, log_file: str):
        """Start piping tmux pane output to log file."""
        try:
            result = subprocess.run(
                ['tmux', 'pipe-pane', '-t', session_name, '-o', 
                 f'cat >> {log_file}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise TmuxError(f"Failed to start logging: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout starting logging for '{session_name}'")
    
    @staticmethod
    def capture_pane(session_name: str, num_lines: int = 200) -> str:
        """Capture visible pane content."""
        try:
            result = subprocess.run(
                ['tmux', 'capture-pane', '-pt', session_name, 
                 '-S', f'-{num_lines}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise TmuxError(f"Failed to capture pane: {result.stderr}")
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout capturing pane for '{session_name}'")
    
    @staticmethod
    def kill_session(session_name: str):
        """Kill a tmux session."""
        try:
            result = subprocess.run(
                ['tmux', 'kill-session', '-t', session_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Don't raise error if session doesn't exist
            if result.returncode != 0 and 'no session found' not in result.stderr.lower():
                raise TmuxError(f"Failed to kill session: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise TmuxError(f"Timeout killing session '{session_name}'")
    
    @staticmethod
    def list_sessions() -> list:
        """List all tmux sessions."""
        try:
            result = subprocess.run(
                ['tmux', 'list-sessions'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # No sessions exist
                if 'no server running' in result.stderr.lower():
                    return []
                raise TmuxError(f"Failed to list sessions: {result.stderr}")
            
            # Parse output (format: session_name: window_count windows ...)
            sessions = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    session_name = line.split(':')[0]
                    sessions.append(session_name)
            
            return sessions
            
        except subprocess.TimeoutExpired:
            raise TmuxError("Timeout listing sessions")




