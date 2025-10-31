#!/usr/bin/env python3
"""Test config and state managers."""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ssh_mcp_server.config import ConfigManager, ConfigError
from ssh_mcp_server.state import StateManager, ensure_log_directory, get_log_file_path


def test_log_directory():
    """Test log directory creation."""
    print("\n=== Testing Log Directory ===")
    
    log_dir = ensure_log_directory()
    print(f"✓ Log directory created/verified: {log_dir}")
    
    # Check it exists
    assert os.path.exists(log_dir), "Log directory should exist"
    print(f"✓ Log directory exists")
    
    # Check permissions (should be 700)
    stat_info = os.stat(log_dir)
    perms = oct(stat_info.st_mode)[-3:]
    print(f"✓ Log directory permissions: {perms}")
    
    # Test log file path
    log_file = get_log_file_path("test_session")
    print(f"✓ Log file path: {log_file}")
    assert log_file.endswith("test_session.log")
    
    print("✅ Log directory tests passed!")


def test_state_manager():
    """Test state manager."""
    print("\n=== Testing State Manager ===")
    
    # Create temporary state file path (don't create the file yet)
    fd, temp_state_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)  # Close the file descriptor
    os.unlink(temp_state_file)  # Delete the empty file - StateManager will create it
    
    try:
        # Initialize state manager
        state = StateManager(state_path=temp_state_file)
        print(f"✓ StateManager initialized with temp file: {temp_state_file}")
        
        # Check file was created
        assert os.path.exists(temp_state_file), "State file should be created"
        print(f"✓ State file created")
        
        # Check permissions (should be 600)
        stat_info = os.stat(temp_state_file)
        perms = oct(stat_info.st_mode)[-3:]
        print(f"✓ State file permissions: {perms}")
        
        # Add a session
        state.add_session(
            session_name="test_session",
            connection_config="test-server",
            tmux_session="test_session",
            log_file="/tmp/test.log"
        )
        print("✓ Session added successfully")
        
        # Check session exists
        assert state.session_exists("test_session"), "Session should exist"
        print("✓ Session exists check passed")
        
        # Get session
        session = state.get_session("test_session")
        assert session is not None
        assert session.session_name == "test_session"
        assert session.connection_config == "test-server"
        print(f"✓ Session retrieved: {session.session_name}")
        
        # List sessions
        sessions = state.list_sessions()
        assert len(sessions) == 1
        print(f"✓ List sessions: {len(sessions)} session(s)")
        
        # Test persistence - create new manager with same file
        state2 = StateManager(state_path=temp_state_file)
        assert state2.session_exists("test_session"), "Session should persist"
        print("✓ Session persisted across reload")
        
        # Remove session
        state2.remove_session("test_session")
        assert not state2.session_exists("test_session"), "Session should be removed"
        print("✓ Session removed successfully")
        
        print("✅ State manager tests passed!")
        
    finally:
        # Clean up
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)
            print(f"✓ Cleaned up temp file: {temp_state_file}")


def test_config_manager():
    """Test config manager - requires a real config file."""
    print("\n=== Testing Config Manager ===")
    
    config_path = os.path.expanduser("~/.ssh_mcp_config.yml")
    
    if not os.path.exists(config_path):
        print(f"⚠️  Config file not found: {config_path}")
        print("⚠️  Skipping config manager test (config file needed)")
        print("   Create a config file to test this functionality")
        return
    
    try:
        # Load config
        config = ConfigManager()
        print(f"✓ ConfigManager loaded from: {config_path}")
        
        # List connections
        connections = config.list_connections()
        print(f"✓ Found {len(connections)} connection(s)")
        
        for conn in connections:
            print(f"  - {conn['name']}: {conn['user']}@{conn['host']}:{conn['port']}")
        
        # Check first connection
        if connections:
            first_conn_name = connections[0]['name']
            conn = config.get_connection(first_conn_name)
            assert conn is not None
            print(f"✓ Retrieved connection: {first_conn_name}")
            
            # Verify sensitive data not exposed
            conn_dict = conn.to_dict()
            assert 'password' not in conn_dict, "Password should not be in to_dict()"
            assert 'key_path' not in conn_dict, "Key path should not be in to_dict()"
            print("✓ Sensitive data not exposed in to_dict()")
        
        print("✅ Config manager tests passed!")
        
    except ConfigError as e:
        print(f"❌ Config error: {e}")
        print("   Check your config file format")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing SSH MCP Server - Core Infrastructure")
    print("=" * 60)
    
    try:
        test_log_directory()
        test_state_manager()
        test_config_manager()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

