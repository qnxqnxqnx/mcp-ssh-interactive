#!/usr/bin/env python3
"""SSH MCP Server - Main entry point."""

import sys
import asyncio
import logging
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp import types

from .config import ConfigManager, ConfigError
from .state import StateManager
from .ssh_session import SSHSessionManager
from .tmux_wrapper import TmuxWrapper

from .tools.list_configs import list_available_configs
from .tools.connection import (
    open_connection_tool,
    close_connection_tool,
    list_connections_tool
)
from .tools.execution import (
    execute_command_tool
)
from .tools.terminal import (
    get_terminal_output_tool,
    interrupt_command_tool
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# Global managers (initialized in main)
config_manager: ConfigManager = None
state_manager: StateManager = None
session_manager: SSHSessionManager = None

# Create MCP server
server = Server("mcp-ssh-interactive")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available MCP tools."""
    return [
        types.Tool(
            name="list_available_configs",
            description="Lists all available SSH server configurations that you can connect to. Use this to discover what remote servers are available before opening a connection. Returns connection names, hosts, and descriptions for each configured server.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="open_connection",
            description="Opens a new SSH connection to a remote server and creates a persistent tmux session for it. You must provide a connection_config_name (from list_available_configs) and a unique session_name. The session will remain active until you explicitly close it. Use the session_name to execute commands and manage this connection.",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_config_name": {
                        "type": "string",
                        "description": "Name of the connection configuration (from list_available_configs)"
                    },
                    "session_name": {
                        "type": "string",
                        "description": "Unique name for this session (alphanumeric, underscores, hyphens only)"
                    }
                },
                "required": ["connection_config_name", "session_name"]
            }
        ),
        types.Tool(
            name="list_connections",
            description="Lists all currently active SSH sessions. Shows session names, connection details, and status for each session. Use this to see what connections you have open and their current state.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="execute_command",
            description="Executes a command on a remote server via SSH. The command is sent to the terminal immediately and this function returns right away. To see the command output and check if it has completed, use get_terminal_output after a reasonable wait time. Look for the command prompt (e.g., '$', '#', or your custom prompt) to return in the output, which indicates the command has finished - just like a human would do when working in a terminal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_name": {
                        "type": "string",
                        "description": "Name of the session to execute command in"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute on the remote server"
                    }
                },
                "required": ["session_name", "command"]
            }
        ),
        types.Tool(
            name="get_terminal_output",
            description="Captures the current visible terminal output (like taking a screenshot of the terminal). Use this after executing a command to see the output and check if the command has completed. Look for the command prompt returning (e.g., '$', '#') to confirm the command finished. This is the primary way to retrieve command results and monitor command execution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_name": {
                        "type": "string",
                        "description": "Name of the session"
                    },
                    "num_lines": {
                        "type": "integer",
                        "description": "Number of lines to retrieve (default: 200)",
                        "default": 200
                    }
                },
                "required": ["session_name"]
            }
        ),
        types.Tool(
            name="interrupt_command",
            description="Sends Ctrl+C signal to the remote terminal to interrupt a running command. Use this when a command is taking too long or appears stuck. The function returns immediately after sending the signal - wait a moment (1-2 seconds) then check get_terminal_output to verify the command was interrupted.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_name": {
                        "type": "string",
                        "description": "Name of the session"
                    }
                },
                "required": ["session_name"]
            }
        ),
        types.Tool(
            name="close_connection",
            description="Closes an SSH connection and terminates the tmux session. Call this when you're done working with a remote server to clean up resources. The log file is preserved for later review if needed. Any running commands in this session will be terminated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_name": {
                        "type": "string",
                        "description": "Name of the session to close"
                    }
                },
                "required": ["session_name"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool execution requests."""
    
    if arguments is None:
        arguments = {}
    
    try:
        # Route to appropriate tool handler
        if name == "list_available_configs":
            result = list_available_configs(config_manager)
        
        elif name == "open_connection":
            result = open_connection_tool(
                session_manager,
                arguments.get("connection_config_name"),
                arguments.get("session_name")
            )
        
        elif name == "list_connections":
            result = list_connections_tool(session_manager)
        
        elif name == "close_connection":
            result = close_connection_tool(
                session_manager,
                arguments.get("session_name")
            )
        
        elif name == "execute_command":
            result = execute_command_tool(
                session_manager,
                arguments.get("session_name"),
                arguments.get("command")
            )
        
        elif name == "get_terminal_output":
            result = get_terminal_output_tool(
                session_manager,
                arguments.get("session_name"),
                arguments.get("num_lines", 200)
            )
        
        elif name == "interrupt_command":
            result = interrupt_command_tool(
                session_manager,
                arguments.get("session_name")
            )
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Convert result to JSON string
        import json
        result_text = json.dumps(result, indent=2)
        
        return [types.TextContent(type="text", text=result_text)]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {"error": f"Tool execution failed: {str(e)}"}
        import json
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Main entry point for the MCP server."""
    global config_manager, state_manager, session_manager
    
    # Check tmux is installed
    if not TmuxWrapper.check_tmux_installed():
        logger.error("tmux is not installed or not accessible")
        sys.exit(1)
    
    # Initialize managers
    try:
        logger.info("Initializing configuration manager...")
        config_manager = ConfigManager()
        logger.info(f"Loaded {len(config_manager.connections)} connection configs")
        
        logger.info("Initializing state manager...")
        state_manager = StateManager()
        logger.info(f"Found {len(state_manager.sessions)} existing sessions")
        
        logger.info("Initializing session manager...")
        session_manager = SSHSessionManager(config_manager, state_manager)
        
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        sys.exit(1)
    
    # Run the server
    logger.info("Starting MCP SSH Interactive Server...")
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-ssh-interactive",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


def run():
    """Entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()


