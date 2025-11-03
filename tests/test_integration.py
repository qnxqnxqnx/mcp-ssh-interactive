#!/usr/bin/env python3
"""Integration test - verify all components work together."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Module Imports ===")
    
    try:
        from ssh_mcp_server import (
            ConfigManager,
            StateManager,
            SSHSessionManager,
            TmuxWrapper
        )
        print("✓ Main module imports successful")
        
        from ssh_mcp_server.config import ConfigError, ConnectionConfig
        print("✓ Config module imports successful")
        
        from ssh_mcp_server.state import StateError, SessionState
        print("✓ State module imports successful")
        
        from ssh_mcp_server.ssh_session import SSHSessionError
        print("✓ SSH session module imports successful")
        
        from ssh_mcp_server.tmux_wrapper import TmuxError
        print("✓ Tmux wrapper module imports successful")
        
        from ssh_mcp_server.tools import (
            list_available_configs,
            open_connection_tool,
            close_connection_tool,
            list_connections_tool,
            execute_command_tool,
            get_terminal_output_tool,
            interrupt_command_tool,
            get_server_info_tool
        )
        print("✓ All tools imported successfully")
        
        print("✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_server_initialization():
    """Test that server module can be imported."""
    print("\n=== Testing Server Module ===")
    
    try:
        from ssh_mcp_server import server
        print("✓ Server module imported")
        
        assert hasattr(server, 'main'), "Server should have main function"
        print("✓ Server has main() function")
        
        assert hasattr(server, 'server'), "Server should have server instance"
        print("✓ Server has server instance")
        
        assert hasattr(server, 'handle_list_tools'), "Server should have handle_list_tools"
        print("✓ Server has handle_list_tools()")
        
        assert hasattr(server, 'handle_call_tool'), "Server should have handle_call_tool"
        print("✓ Server has handle_call_tool()")
        
        print("✅ Server module structure verified!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_package_info():
    """Test package metadata."""
    print("\n=== Testing Package Info ===")
    
    try:
        import ssh_mcp_server
        print(f"✓ Package version: {ssh_mcp_server.__version__}")
        print(f"✓ Package location: {ssh_mcp_server.__file__}")
        
        print("✅ Package info verified!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MCP SSH Interactive - Integration Test")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_server_initialization():
        tests_passed += 1
    
    if test_package_info():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    if tests_passed == tests_total:
        print(f"✅ All {tests_total} integration tests passed!")
        print("=" * 60)
        print("\nMCP SSH Interactive is ready for use!")
        print("\nTo start the server:")
        print("  mcp-ssh-interactive")
        print("\nMake sure you have:")
        print("  1. Created ~/.mcp-ssh-interactive/config.yml with your SSH servers")
        print("  2. tmux installed (tmux -V)")
        print("  3. Valid SSH keys with proper permissions")
        sys.exit(0)
    else:
        print(f"❌ {tests_total - tests_passed} test(s) failed")
        print("=" * 60)
        sys.exit(1)




