#!/usr/bin/env python3
"""Test tmux wrapper functionality."""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ssh_mcp_server.tmux_wrapper import TmuxWrapper, TmuxError


def test_tmux_installed():
    """Test that tmux is installed."""
    print("\n=== Testing Tmux Installation ===")
    
    installed = TmuxWrapper.check_tmux_installed()
    if not installed:
        print("❌ tmux is not installed!")
        print("   Please install tmux: sudo apt install tmux")
        sys.exit(1)
    
    print("✓ tmux is installed")
    print("✅ Tmux installation test passed!")


def test_session_operations():
    """Test creating, checking, and killing sessions."""
    print("\n=== Testing Session Operations ===")
    
    test_session = "ssh_mcp_test_session"
    
    # Clean up any existing test session
    try:
        TmuxWrapper.kill_session(test_session)
        time.sleep(0.5)
    except:
        pass
    
    # Verify session doesn't exist
    exists = TmuxWrapper.session_exists(test_session)
    assert not exists, "Session should not exist initially"
    print("✓ Session doesn't exist initially")
    
    # Create session
    TmuxWrapper.create_session(test_session)
    print(f"✓ Created session: {test_session}")
    
    # Verify session exists
    exists = TmuxWrapper.session_exists(test_session)
    assert exists, "Session should exist after creation"
    print("✓ Session exists after creation")
    
    # Set history limit
    TmuxWrapper.set_history_limit(test_session, 200000)
    print("✓ Set history limit")
    
    # List sessions
    sessions = TmuxWrapper.list_sessions()
    assert test_session in sessions, "Session should be in list"
    print(f"✓ Session appears in list: {sessions}")
    
    # Kill session
    TmuxWrapper.kill_session(test_session)
    print("✓ Killed session")
    
    # Verify session is gone
    time.sleep(0.5)
    exists = TmuxWrapper.session_exists(test_session)
    assert not exists, "Session should not exist after killing"
    print("✓ Session doesn't exist after killing")
    
    print("✅ Session operations test passed!")


def test_send_commands():
    """Test sending commands to a session."""
    print("\n=== Testing Command Sending ===")
    
    test_session = "ssh_mcp_test_cmd"
    
    # Clean up any existing test session
    try:
        TmuxWrapper.kill_session(test_session)
        time.sleep(0.5)
    except:
        pass
    
    # Create session
    TmuxWrapper.create_session(test_session)
    print(f"✓ Created session: {test_session}")
    
    # Send a simple command
    TmuxWrapper.send_command(test_session, "echo 'Hello from tmux'")
    print("✓ Sent echo command")
    
    # Wait for command to execute
    time.sleep(0.5)
    
    # Capture pane output
    output = TmuxWrapper.capture_pane(test_session, num_lines=50)
    print("✓ Captured pane output")
    print(f"   Output preview: {output[:100]}...")
    
    # Verify we got some output
    assert len(output) > 0, "Should capture some output"
    assert "Hello from tmux" in output, "Should find our echo message"
    print("✓ Found expected output in captured pane")
    
    # Send Ctrl+C
    TmuxWrapper.send_ctrl_c(test_session)
    print("✓ Sent Ctrl+C")
    
    # Clean up
    TmuxWrapper.kill_session(test_session)
    print("✓ Cleaned up session")
    
    print("✅ Command sending test passed!")


def test_logging():
    """Test logging to a file."""
    print("\n=== Testing Logging ===")
    
    test_session = "ssh_mcp_test_log"
    log_file = "/tmp/ssh_mcp_test.log"
    
    # Clean up
    try:
        TmuxWrapper.kill_session(test_session)
        time.sleep(0.5)
    except:
        pass
    
    if os.path.exists(log_file):
        os.unlink(log_file)
    
    # Create session
    TmuxWrapper.create_session(test_session)
    print(f"✓ Created session: {test_session}")
    
    # Start logging
    TmuxWrapper.start_logging(test_session, log_file)
    print(f"✓ Started logging to: {log_file}")
    
    # Send commands with markers
    TmuxWrapper.send_command(test_session, "echo '__BEGIN__test123__'")
    TmuxWrapper.send_command(test_session, "echo 'Test output'")
    TmuxWrapper.send_command(test_session, "echo '__END__test123__'")
    print("✓ Sent commands with markers")
    
    # Wait for output to be logged
    time.sleep(1)
    
    # Check log file exists
    assert os.path.exists(log_file), "Log file should exist"
    print("✓ Log file created")
    
    # Read log file
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    print(f"✓ Log file size: {len(log_content)} bytes")
    
    # Verify markers are in log
    assert "__BEGIN__test123__" in log_content, "Should find BEGIN marker"
    assert "__END__test123__" in log_content, "Should find END marker"
    assert "Test output" in log_content, "Should find test output"
    print("✓ Found all markers and output in log file")
    
    # Clean up
    TmuxWrapper.kill_session(test_session)
    os.unlink(log_file)
    print("✓ Cleaned up session and log file")
    
    print("✅ Logging test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing SSH MCP Server - Tmux Integration")
    print("=" * 60)
    
    try:
        test_tmux_installed()
        test_session_operations()
        test_send_commands()
        test_logging()
        
        print("\n" + "=" * 60)
        print("✅ All tmux tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except TmuxError as e:
        print(f"\n❌ Tmux error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




