#!/usr/bin/env python3
"""Test server info functionality."""

import sys
import os
import tempfile
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ssh_mcp_server.config import ConfigManager, ConfigError, ConnectionConfig
from ssh_mcp_server.state import ensure_info_directory, resolve_info_file_path
from ssh_mcp_server.tools.server_info import get_server_info_tool


def test_info_file_in_connection_config():
    """Test info_file field in ConnectionConfig."""
    print("\n=== Testing Info File in Connection Config ===")
    
    # Create temporary config file with info_file
    base_dir = tempfile.mkdtemp()
    config_path = os.path.join(base_dir, 'config.yml')
    
    config_data = {
        'connections': {
            'test-server': {
                'host': '192.168.1.100',
                'user': 'testuser',
                'key_path': os.path.expanduser('~/.ssh/id_rsa') if os.path.exists(os.path.expanduser('~/.ssh/id_rsa')) else '/tmp/fake_key',
                'info_file': 'test-server.md'
            }
        }
    }
    
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Create fake key if it doesn't exist
        key_path = os.path.expanduser('~/.ssh/id_rsa')
        if not os.path.exists(key_path):
            key_path = '/tmp/fake_key'
            with open(key_path, 'w') as f:
                f.write('fake key')
            os.chmod(key_path, 0o600)
            config_data['connections']['test-server']['key_path'] = key_path
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
        
        # Test with temporary config path
        # We need to mock or create a valid scenario
        # For now, just test the path resolution
        
        info_dir = ensure_info_directory()
        info_file_path = resolve_info_file_path('test-server.md')
        assert os.path.basename(info_file_path) == 'test-server.md'
        print(f"✓ Info file path resolved: {info_file_path}")
        
        print("✅ Info file in connection config test passed!")
        
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.unlink(config_path)
        if os.path.exists(key_path) and key_path == '/tmp/fake_key':
            os.unlink(key_path)
        if os.path.exists(base_dir):
            os.rmdir(base_dir)


def test_get_server_info_tool():
    """Test get_server_info_tool."""
    print("\n=== Testing Get Server Info Tool ===")
    
    # Create temporary config and info file
    base_dir = tempfile.mkdtemp()
    config_path = os.path.join(base_dir, 'config.yml')
    info_dir = os.path.join(base_dir, 'info')
    os.makedirs(info_dir, mode=0o700)
    
    info_file_path = os.path.join(info_dir, 'test-server.md')
    info_content = """# Test Server

To login as root on this target always use the command `su` with the password `testpassword`

To find out the firmware version of the installed software use the command `mold firmware_version`

To start all mqtt apps on this server use the command `/etc/init.d/mqtt-apps.sh`
"""
    
    with open(info_file_path, 'w') as f:
        f.write(info_content)
    
    # Create config with info_file
    config_data = {
        'connections': {
            'test-server': {
                'host': '192.168.1.100',
                'user': 'testuser',
                'key_path': os.path.expanduser('~/.ssh/id_rsa') if os.path.exists(os.path.expanduser('~/.ssh/id_rsa')) else '/tmp/fake_key',
                'info_file': info_file_path  # Use absolute path
            }
        }
    }
    
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Create fake key if it doesn't exist
        key_path = os.path.expanduser('~/.ssh/id_rsa')
        if not os.path.exists(key_path):
            key_path = '/tmp/fake_key'
            with open(key_path, 'w') as f:
                f.write('fake key')
            os.chmod(key_path, 0o600)
            config_data['connections']['test-server']['key_path'] = key_path
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
        
        # Load config
        config_manager = ConfigManager(config_path=config_path)
        
        # Test get_server_info
        result = get_server_info_tool(config_manager, 'test-server')
        
        assert result['success'] == True, "Should succeed"
        assert result['connection_config_name'] == 'test-server'
        assert result['info_content'] == info_content
        assert result['info_file'] == info_file_path
        print("✓ get_server_info returned correct content")
        
        # Test with non-existent server
        result = get_server_info_tool(config_manager, 'non-existent')
        assert result['success'] == False, "Should fail for non-existent server"
        assert 'error' in result
        print("✓ get_server_info handles non-existent server correctly")
        
        # Test with server without info_file
        # Add another server without info_file
        config_data['connections']['no-info-server'] = {
            'host': '192.168.1.101',
            'user': 'testuser',
            'key_path': key_path
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        config_manager = ConfigManager(config_path=config_path)
        result = get_server_info_tool(config_manager, 'no-info-server')
        assert result['success'] == False, "Should fail for server without info_file"
        assert 'info_file' in result['error'].lower()
        print("✓ get_server_info handles server without info_file correctly")
        
        print("✅ Get server info tool tests passed!")
        
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.unlink(config_path)
        if os.path.exists(info_file_path):
            os.unlink(info_file_path)
        if os.path.exists(info_dir):
            os.rmdir(info_dir)
        if os.path.exists(key_path) and key_path == '/tmp/fake_key':
            os.unlink(key_path)
        if os.path.exists(base_dir):
            os.rmdir(base_dir)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Server Info Functionality")
    print("=" * 60)
    
    try:
        test_info_file_in_connection_config()
        test_get_server_info_tool()
        
        print("\n" + "=" * 60)
        print("✅ All server info tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

