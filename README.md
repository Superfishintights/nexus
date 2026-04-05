# Nexus MCP Server

Nexus is a code-mode Model Context Protocol (MCP) server. Core runtime and tool packs are now split for distribution:

- `nexus-core`: MCP server/runtime (`nexus/`)
- Tool packs: separate Python packages with distinct import roots

This repo remains a monorepo for development.

## Requirements

- Python `>= 3.10` (see `nexus/pyproject.toml`)

## Install

Install core:

```bash
pip install -e ./nexus
```

Install only the tool packs you want:

```bash
pip install -e ./tool_packs/nexus_tools_jira
pip install -e ./tool_packs/nexus_tools_n8n
```

## Configure Tool Discovery

Nexus no longer assumes a built-in `tools` package by default.
Set `NEXUS_TOOL_PACKAGES` to the installed package roots:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_jira,nexus_tools_n8n"
```

You can also set this in `.env`.

## Run

```bash
python nexus/server.py
```

## Self-test (stdlib only)

```bash
python nexus/selftest.py
```

## Configuration (cross-platform)

Nexus reads settings from:

1) Process environment variables
2) A `.env` file

Supported `.env` locations (lowest precedence to highest):

- User config:
  - Linux: `~/.config/nexus/.env` (or `$XDG_CONFIG_HOME/nexus/.env`)
  - macOS: `~/Library/Application Support/nexus/.env`
  - Windows: `%APPDATA%\\nexus\\.env`
- Project-local: `./.env`

Override lookup with `NEXUS_ENV_FILE`.

## Tool Pack Import Roots

Current first-party pack roots:

- `nexus_tools_jira`
- `nexus_tools_n8n`
- `nexus_tools_sonarr`
- `nexus_tools_radarr`
- `nexus_tools_tautulli`
- `nexus_tools_starling`

## MCP Client Setup

Nexus is a stdio MCP server. Configure your client to run:

- Command: `python`
- Args: `nexus/server.py`
- Working directory: repo root

```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["nexus/server.py"],
      "cwd": "/absolute/path/to/nexus-repo"
    }
  }
}
```
