## MCP SSH Interactive

An MCP (Model Context Protocol) server that enables AI agents to run fully interactive SSH sessions (via tmux) and execute commands like a human operator.

### Features

- **Interactive SSH via tmux**: real terminal behavior, prompts, Ctrl+C, history.
- **Persistent sessions**: sessions survive across tool calls; reconnectable.
- **Multiple concurrent connections**: manage many servers in parallel.
- **Complete output capture**: retrieve terminal buffer reliably.
- **Async commands + polling**: fire-and-check pattern for long tasks.

### Requirements

- **Python**: 3.9+
- **tmux**: 2.6+ (`tmux -V`)
  - Install: `brew install tmux` on macOS, `apt install tmux` / `yum install tmux` / `pacman -S tmux` on Linux
- **OpenSSH client**: 7.0+
- **OS**: Linux or macOS

### Installation

**For end users** (just want to use the MCP server):

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-ssh-interactive.git
cd mcp-ssh-interactive

# Install with pip
pip install .
```

Or using pipx for an isolated environment (recommended):

```bash
# Install with pipx
pipx install .
```

**For developers** (working on the code):

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-ssh-interactive.git
cd mcp-ssh-interactive

# Install in editable mode
pip install -e .
```

Note: This package is not currently published to PyPI, so installation from source is required.

### Configuration

Create `~/.mcp-ssh-interactive/config.yml` with your SSH targets:

```yaml
connections:
  my-server:
    host: 192.168.1.100
    user: username
    key_path: ~/.ssh/id_rsa
    port: 22
    description: My remote server
    info_file: my-server.md  # Optional: path to server-specific info file
  prod-db:
    host: db.example.com
    user: deploy
    key_path: ~/.ssh/id_ed25519
    port: 22
    description: Production database host (read-only)
  test-server:
    host: test.example.com
    user: demo
    password: mypassword
    port: 22
    description: Test server with password authentication
```

Notes:
- Either `key_path` or `password` must be provided for authentication
- `key_path` is strongly recommended over `password` for security
- If using `key_path`, it must exist and be readable; typical permissions `chmod 600`
- `~/.mcp-ssh-interactive/config.yml` is required; if missing or invalid the server exits with a clear error
- `info_file` (optional): Path to a markdown file containing server-specific instructions and information. See [Server-Specific Information](#server-specific-information) below.

Schema (informal):
- **connections**: map of connection name → object
  - **host** (string, required)
  - **user** (string, required)
  - **key_path** (string, optional but recommended; `~` expanded; verified to exist)
  - **password** (string, optional; requires either this or `key_path`)
  - **port** (int, default `22`)
  - **description** (string, optional)
  - **info_file** (string, optional): Path to markdown file with server-specific information. Supports:
    - Relative paths (e.g., `my-server.md`) - resolved relative to `~/.mcp-ssh-interactive/info/`
    - Absolute paths starting with `~` (e.g., `~/custom/path/server.md`)
    - Absolute paths starting with `/` (e.g., `/tmp/server.md`)
  
Note: At least one of `key_path` or `password` must be provided. Using `key_path` is strongly recommended for security.

### Server-Specific Information

You can provide server-specific instructions, commands, and important information for each server by creating markdown files and referencing them in your configuration using the `info_file` field.

**Example:**

1. Create a markdown file at `~/.mcp-ssh-interactive/info/my-server.md`:

```markdown
# My Server Instructions

To login as root on this target always use the command `su` with the password specified in the secure vault.

To check the system status use the command `systemctl status important-service`

To restart all application services use the command `/usr/local/bin/restart-services.sh`
```

2. Reference it in your config:

```yaml
connections:
  my-server:
    host: 192.168.1.100
    user: username
    key_path: ~/.ssh/id_rsa
    info_file: my-server.md  # Relative path (resolved to ~/.mcp-ssh-interactive/info/my-server.md)
```

**Info File Path Resolution:**

- **Relative paths** (e.g., `my-server.md`): Resolved relative to `~/.mcp-ssh-interactive/info/`
- **Paths starting with `~`** (e.g., `~/custom/path/server.md`): Treated as absolute paths
- **Paths starting with `/`** (e.g., `/tmp/server.md`): Treated as absolute paths

When you open a connection to a server with an `info_file` configured, the response will include a hint prompting you to call `get_server_info` to retrieve the server-specific information. This information applies to all sessions for a server configuration, so you only need to call it once per server.

### Starting the MCP server

The server runs over stdio and is launched by your MCP client. You can also start it manually:

```bash
mcp-ssh-interactive
```

If `tmux` is not installed or config is invalid, the server exits with an error.

### Using with MCP clients (generic JSON config)

Add an entry for this server in your MCP client configuration. The generic structure is:

```json
{
  "mcpServers": {
    "mcp-ssh-interactive": {
      "command": "mcp-ssh-interactive"
    }
  }
}
```

Different MCP clients might use different configuration file formats and locations. Please check the relevant documentation for your specific MCP client to determine where and how to add MCP server configurations.

After adding, restart or reload your client so it can discover the new server.

### Available tools and typical workflow

The server exposes the following tools:
- **list_available_configs**: discover connection names from `~/.mcp-ssh-interactive/config.yml`.
- **open_connection**: start SSH + tmux logging under a unique `session_name`. After successfully opening a connection, check if the server has additional information by calling `get_server_info` with the connection_config_name.
- **list_connections**: view active sessions and their status.
- **execute_command**: send a command to the remote terminal (returns immediately).
- **get_terminal_output**: capture the visible terminal buffer (poll for completion).
- **interrupt_command**: send Ctrl+C to stop a running process.
- **close_connection**: terminate tmux session and remove from state.
- **get_server_info**: retrieve server-specific information and instructions for a connection configuration. Use this after opening a connection to learn about server-specific procedures, commands, and important information. The information applies to all sessions for a server configuration, so you only need to call it once per server configuration.

### File Structure

All files are stored in `~/.mcp-ssh-interactive/`:

```
~/.mcp-ssh-interactive/
├── config.yml           # SSH connection configurations
├── state.json           # Active session state
├── logs/                # Session logs
│   └── <session_name>.log
└── info/                # Server-specific info files
    └── <server-name>.md
```

**Files:**
- **config.yml**: SSH connection configurations with host, user, keys, and optional `info_file` references
- **state.json**: Tracks active sessions, their tmux names, log file paths, and timestamps
- **logs/**: Directory containing session logs (one per active session)
  - tmux pipes pane output to these files from the moment the connection opens
  - Files are created with directory permissions `700`; rotate/prune as needed
- **info/**: Directory for server-specific information files (markdown format)
  - Referenced via `info_file` field in config.yml
  - Can use relative paths (e.g., `my-server.md`) or absolute paths

All files are local to the machine running the MCP server (your workstation).

### Troubleshooting

- "tmux is not installed or not accessible"
  - Install tmux (`brew install tmux` on macOS, `apt/yum/pacman` on Linux) and ensure it's in `$PATH`.

- "Configuration file not found" or "Configuration is empty"
  - Create `~/.mcp-ssh-interactive/config.yml` as shown above; verify correct YAML.

- "Key file not found" or SSH failures (permission denied, host key verification)
  - Check `key_path` exists and has `chmod 600`.
  - Ensure `ssh -i <key> user@host` works outside of MCP.
  - Pre-accept host keys with a first manual SSH or configure `known_hosts`.

- No logs written
  - Confirm `~/.mcp-ssh-interactive/logs/` exists and is writable; server creates it automatically.
  - Confirm your `session_name` and check the matching log path.

- "Info file not found" error when calling `get_server_info`
  - Check that the `info_file` path in your config is correct.
  - For relative paths, ensure the file exists in `~/.mcp-ssh-interactive/info/`.
  - Verify the file has proper read permissions.

### Security considerations

- Never commit `~/.mcp-ssh-interactive/config.yml` or private keys to source control.
- Limit privileges of the SSH users you automate.
- Treat `~/.mcp-ssh-interactive/logs/*.log` as sensitive; they may contain command outputs.
- Treat `~/.mcp-ssh-interactive/info/*.md` as sensitive if they contain passwords or sensitive information.

### Development

Run simple integration checks:
```bash
python tests/test_integration.py
```

### License

MIT





