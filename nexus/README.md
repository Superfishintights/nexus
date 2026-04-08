# nexus-core

Core runtime package for the Nexus MCP server.

This package contains:

- MCP server/runtime code under `nexus/`
- lazy tool discovery and policy enforcement
- runner and execution worker support

## Execution boundary

Phase 1 keeps the host/runner contract explicit:

- `server.py` is the host boundary. It owns MCP entrypoints, tool discovery,
  active policy resolution, and the decision to execute model-authored code.
- `runner.py` builds the execution globals for snippets (`RESULT`,
  `RUNNER_SETTINGS`, `TOOLS`, `load_tool`) and launches the isolated execution
  worker.
- `execution_worker.py` is the bounded subprocess entrypoint for snippet
  execution.
- `tool_catalog.py`, `tool_registry.py`, and `tool_policy.py` stay on the host
  side of the boundary so approved tool access continues to flow through Nexus
  policy checks instead of direct runner imports.

In restricted mode, snippets lose `__import__`, only canonical allowed tools can
be loaded, and approved tool calls still succeed through `load_tool(...)`.

Tool integrations are distributed separately as installable tool-pack packages such as:

- `nexus-tools-jira`
- `nexus-tools-n8n`
- `nexus-tools-sonarr`
- `nexus-tools-radarr`
- `nexus-tools-tautulli`
- `nexus-tools-starling`

Configure installed tool packs with `NEXUS_TOOL_PACKAGES`, for example:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_jira,nexus_tools_n8n"
```

For full monorepo documentation, see the repository root `README.md`.
