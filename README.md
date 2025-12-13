# Nexus MCP Server

Nexus is a “code‑mode” Model Context Protocol (MCP) server. It exposes a small
MCP surface (`run_code`, `search_tools`, `get_tool`) while letting models
orchestrate many domain tools programmatically in Python.

## Requirements

- Python `>= 3.10` (see `nexus/pyproject.toml`)

## Install

```bash
pip install -e ./nexus
```

If you prefer a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ./nexus
```

## Run

```bash
python nexus/server.py
```

## Configuration (cross-platform)

Nexus reads settings from:

1) Process environment variables
2) A `.env` file (recommended for portability across shells/OS)

Supported `.env` locations (lowest precedence → highest):

- User config:
  - Linux: `~/.config/nexus/.env` (or `$XDG_CONFIG_HOME/nexus/.env`)
  - macOS: `~/Library/Application Support/nexus/.env`
  - Windows: `%APPDATA%\\nexus\\.env`
- Project-local: `./.env` (current working directory)

Override the search path by setting `NEXUS_ENV_FILE` to an explicit file path.

Notes:

- `.env` changes are picked up automatically (no server restart needed).
- Tool discovery is refreshed on each `search_tools`/`get_tool`/`run_code` call, so adding tool files/packages does not require a restart.

## Tool Packages

Nexus discovers tools by scanning Python packages for functions decorated with
`@register_tool`. By default it scans the built‑in `tools` package.

For large multi-service installs, prefer `@register_tool(namespace="service")` so tool
names are unambiguous (e.g., `jira.get_issue_status`).

Notes:

- Discovery is via AST parsing (no imports). Tool modules must be valid Python; files
  with syntax errors are skipped and their tools won’t be discoverable.
- Tool file layout does not affect MCP “context bloat” (results are filtered by
  `search_tools`/`get_tool`), but it does affect scan/import performance. See
  `tools/ADDING_TOOLSETS.md`.

To add external tool packages, install them on the machine and set:

```bash
export NEXUS_TOOL_PACKAGES="tools,company_tools,generated_tools"
```

Tools are loaded lazily: use `search_tools` to find what you need, and import or
`load_tool("tool_name")` inside `run_code`.

## MCP Client Setup (examples)

Nexus is a stdio MCP server. Configure your MCP client to run:

- Command: `python`
- Args: `nexus/server.py`
- Working directory: the repo root (so `./.env` and local tool packages are available)

**JSON example**

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

**TOML example**

```toml
[mcp.servers.nexus]
command = "python"
args = ["nexus/server.py"]
cwd = "/absolute/path/to/nexus-repo"
```
