# Tools

This repository includes built-in toolsets for Jira, n8n, Sonarr, Radarr, and Tautulli.
Some are hand-authored, some are generated, and Nexus discovers all of them lazily.

For larger toolsets (dozens/hundreds of tools), keep them in separate packages and have
Nexus discover them lazily via `NEXUS_TOOL_PACKAGES`.

See `tools/ADDING_TOOLSETS.md` for a copy/paste-friendly template and conventions.

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

Radarr tools require:

- `RADARR_URL`: Base URL for your Radarr instance (e.g., `https://radarr.example.com`)
- `RADARR_API_KEY`: API key for Radarr (`RADARR_TOKEN` is accepted as a legacy fallback)

Built-in Tautulli tools include a curated semantic layer in `tools/tautulli/api.py` plus
generated endpoint wrappers under `tools/tautulli/`. Canonical names are namespaced
(for example `tautulli.get_activity`) and compatibility aliases remain available where
explicitly defined.

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
    examples=["jira.get_issue_status('PROJ-123')"],
)
def get_issue_status(issue_key: str) -> dict:
    client = get_client()
    issue = client._make_request(f"issue/{issue_key}")
    return {
        "key": issue_key,
        "status": issue["fields"]["status"]["name"],
    }
```

Notes:

- Prefer `namespace="service"` for large multi-service installs to avoid name collisions
  (e.g., `jira.get_issue_status`).
- If you rename a tool (e.g., to introduce namespacing), preserve compatibility with
  `aliases=[...]` so older names can still be loaded.
- Keep `name=...`, `namespace=...`, `description=...`, and `examples=[...]` as **literal**
  strings/lists if you want them to be discoverable via AST scanning (without importing).
- Avoid side effects at import time (no network calls at module import).

### Tool Organization (one file vs many)

Nexus keeps MCP context small via `search_tools`/`get_tool` (filtered results). File
layout mainly impacts maintainability and runtime behavior:

- Small toolsets (≈1–20 tools, or a few hundred LOC): keep a single `tools/<service>/api.py`.
- Medium toolsets: split into a handful of modules by resource area (e.g.,
  `workflows.py`, `executions.py`).
- Large/generated toolsets: split into subpackages (or ship as separate packages via
  `NEXUS_TOOL_PACKAGES`).

Trade-offs:

- Fewer files ⇒ faster catalog scan, but `load_tool` imports/registers more at once.
- More files ⇒ slower scan, but finer-grained lazy imports.

### Tool Discovery Requires Valid Python

Tool discovery uses `ast.parse` and silently skips files with syntax errors. If a tool
doesn’t show up in `search_tools`, validate that its module is syntactically valid:

```bash
python -m py_compile tools/<service>/*.py
```

### Optional: Typed Settings (`RUNNER_SETTINGS`)

Tools typically read env values directly via `nexus.config.get_setting` (as the built-in
Tautulli/Sonarr clients do). The `nexus/settings/*` modules are an optional convenience
to expose validated, typed configuration to `run_code` snippets via `RUNNER_SETTINGS`;
they are not required for tool discovery or tool execution.

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
