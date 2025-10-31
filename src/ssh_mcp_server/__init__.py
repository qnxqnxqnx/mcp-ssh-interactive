"""SSH MCP Server - Remote command execution via SSH."""

__version__ = "1.0.0"

from .server import main
from .config import ConfigManager
from .state import StateManager
from .ssh_session import SSHSessionManager
from .tmux_wrapper import TmuxWrapper

__all__ = [
    "main",
    "ConfigManager",
    "StateManager",
    "SSHSessionManager",
    "TmuxWrapper",
]




