#!/usr/bin/env python3
"""Test SSH session manager (structure validation, no real SSH connection)."""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ssh_mcp_server.config import ConfigManager
from ssh_mcp_server.state import StateManager
from ssh_mcp_server.ssh_session import SSHSessionManager, SSHSessionError


def test_session_manager_initialization():
    """Test SSH session manager initialization."""
    print("\n=== Testing SSH Session Manager Initialization ===")
    
    # Use existing config (from earlier tests)
    config_path = os.path.expanduser("~/.ssh_mcp_config.yml")
    if not os.path.exists(config_path):
        print("⚠️  No config file found, skipping test")
        return
    
    # Create temp state file
    fd, temp_state_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(temp_state_file)
    
    try:
        config = ConfigManager(config_path)
        state = StateManager(state_path=temp_state_file)
        
        session_manager = SSHSessionManager(config, state)
        print("✓ SSHSessionManager initialized")
        
        # Verify it has the right attributes
        assert hasattr(session_manager, 'config')
        assert hasattr(session_manager, 'state')
        assert hasattr(session_manager, 'tmux')
        print("✓ Session manager has required attributes")
        
        # Test list_connections with empty state
        result = session_manager.list_connections()
        assert result['total'] == 0
        assert result['sessions'] == []
        print("✓ list_connections() works with empty state")
        
        print("✅ SSH session manager initialization test passed!")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_session_validation():
    """Test session name validation."""
    print("\n=== Testing Session Name Validation ===")
    
    config_path = os.path.expanduser("~/.ssh_mcp_config.yml")
    if not os.path.exists(config_path):
        print("⚠️  No config file found, skipping test")
        return
    
    fd, temp_state_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(temp_state_file)
    
    try:
        config = ConfigManager(config_path)
        state = StateManager(state_path=temp_state_file)
        session_manager = SSHSessionManager(config, state)
        
        # Get first available config
        configs = config.list_connections()
        if not configs:
            print("⚠️  No connections in config, skipping test")
            return
        
        first_config_name = configs[0]['name']
        
        # Test invalid session names
        invalid_names = [
            'session with spaces',
            'session@special',
            'session.dot',
            'session/slash',
            'session\\backslash'
        ]
        
        for invalid_name in invalid_names:
            try:
                session_manager.open_connection(first_config_name, invalid_name)
                assert False, f"Should have rejected invalid name: {invalid_name}"
            except SSHSessionError as e:
                assert 'Invalid session name' in str(e)
                print(f"✓ Rejected invalid name: {invalid_name}")
        
        # Test invalid config name
        try:
            session_manager.open_connection('non-existent-config', 'valid-session')
            assert False, "Should have rejected non-existent config"
        except SSHSessionError as e:
            assert 'not found' in str(e)
            assert 'Available:' in str(e)
            print("✓ Rejected non-existent config with helpful message")
        
        # Test closing non-existent session
        try:
            session_manager.close_connection('non-existent-session')
            assert False, "Should have rejected non-existent session"
        except SSHSessionError as e:
            assert 'not found' in str(e)
            print("✓ Rejected closing non-existent session")
        
        print("✅ Session validation test passed!")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_ssh_command_building():
    """Test SSH command building."""
    print("\n=== Testing SSH Command Building ===")
    
    config_path = os.path.expanduser("~/.ssh_mcp_config.yml")
    if not os.path.exists(config_path):
        print("⚠️  No config file found, skipping test")
        return
    
    fd, temp_state_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(temp_state_file)
    
    try:
        config = ConfigManager(config_path)
        state = StateManager(state_path=temp_state_file)
        session_manager = SSHSessionManager(config, state)
        
        # Get first connection config
        configs = config.list_connections()
        if not configs:
            print("⚠️  No connections in config, skipping test")
            return
        
        first_config_name = configs[0]['name']
        conn_config = config.get_connection(first_config_name)
        
        # Build SSH command
        ssh_cmd = session_manager._build_ssh_command(conn_config)
        print(f"✓ Built SSH command: {ssh_cmd}")
        
        # Verify command structure
        assert 'ssh' in ssh_cmd
        assert '-tt' in ssh_cmd
        assert '-i' in ssh_cmd
        assert conn_config.key_path in ssh_cmd
        assert f'{conn_config.user}@{conn_config.host}' in ssh_cmd
        print("✓ SSH command has correct structure")
        
        # Check port handling
        if conn_config.port != 22:
            assert '-p' in ssh_cmd
            assert str(conn_config.port) in ssh_cmd
            print("✓ SSH command includes custom port")
        
        print("✅ SSH command building test passed!")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_session_status():
    """Test session status checking."""
    print("\n=== Testing Session Status ===")
    
    config_path = os.path.expanduser("~/.ssh_mcp_config.yml")
    if not os.path.exists(config_path):
        print("⚠️  No config file found, skipping test")
        return
    
    fd, temp_state_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(temp_state_file)
    
    try:
        config = ConfigManager(config_path)
        state = StateManager(state_path=temp_state_file)
        session_manager = SSHSessionManager(config, state)
        
        # Check status of non-existent session
        status = session_manager.get_session_status('non-existent')
        assert status == 'not_found'
        print("✓ Non-existent session status: 'not_found'")
        
        print("✅ Session status test passed!")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing SSH MCP Server - SSH Session Manager")
    print("=" * 60)
    print("\nNOTE: These tests validate structure and validation logic.")
    print("Full SSH connection testing requires a real SSH server.")
    
    try:
        test_session_manager_initialization()
        test_session_validation()
        test_ssh_command_building()
        test_session_status()
        
        print("\n" + "=" * 60)
        print("✅ All SSH session manager tests passed!")
        print("=" * 60)
        print("\nTo test actual SSH connections, you need:")
        print("1. A valid SSH server in ~/.ssh_mcp_config.yml")
        print("2. Valid SSH key with proper permissions")
        print("3. Run: session_manager.open_connection(config_name, session_name)")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




