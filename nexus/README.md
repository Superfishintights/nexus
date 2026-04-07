# nexus-core

Core runtime package for the Nexus MCP server.

This package contains:

- MCP server/runtime code under `nexus/`
- lazy tool discovery and policy enforcement
- runner and execution worker support

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
