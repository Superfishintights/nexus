# Jira Tools

This repository includes a lightweight Jira REST v2 client (`tools/jira/client.py`) and
a small example tool (`tools/jira/get_issue_status.py`). At work you can keep
larger Jira/Sourcegraph/etc toolsets in separate packages and have Nexus discover
them lazily.

## Configuration

Nexus can read configuration from environment variables *or* from a `.env` file.
This is the most reliable way to make tools work across shells/OSes (fish/bash/zsh,
PowerShell/cmd, etc.) without relying on shell startup scripts.

Supported `.env` locations (lowest precedence to highest):

- User config: `~/.config/nexus/.env` (Linux), `~/Library/Application Support/nexus/.env` (macOS), `%APPDATA%\\nexus\\.env` (Windows)
- Project-local: `./.env` (current working directory)

You can also force a specific env file path by setting `NEXUS_ENV_FILE`.

Notes:

- `.env` changes are picked up automatically (no server restart needed).
- `NEXUS_TOOL_PACKAGES` can also be set in `.env` to control tool discovery.

Jira tools require:

- `JIRA_HOSTNAME`: Jira hostname or URL (e.g., `jira.company.com`)
- `JIRA_PAT`: Personal Access Token for authentication

Tautulli tools require:

- `TAUTULLI_URL`: Base URL for your Tautulli instance (e.g., `https://tautulli.example.com`)
- `TAUTULLI_API_KEY`: API key for Tautulli

Built-in Tautulli tools live in `tools/tautulli/api.py` (e.g., `tautulli_get_activity`, `tautulli_get_history`).

## Writing Tools

Tools are single Python functions decorated with `@register_tool`. They may call
external services in either read or write mode; Nexus does not restrict network
access in code execution.

Example:

```python
from nexus.tool_registry import register_tool
from tools.jira.client import get_client

@register_tool(
    description="Get current status for a Jira issue",
    examples=["get_issue_status('PROJ-123')"],
)
def get_issue_status(issue_key: str) -> dict:
    client = get_client()
    issue = client._make_request(f"issue/{issue_key}")
    return {
        "key": issue_key,
        "status": issue["fields"]["status"]["name"],
    }
```

## External Tool Packages

Install any additional tool packages on the machine, then set:

```bash
export NEXUS_TOOL_PACKAGES="tools,company_tools,generated_tools"
```

Nexus will scan these packages for `@register_tool` functions (including subpackages)
and expose them
via `search_tools`/`get_tool` without importing everything up front.

Or put this in `.env`:

```text
NEXUS_TOOL_PACKAGES=tools,company_tools,generated_tools
```
