# Distribution Guide

Nexus now distributes as multiple packages:

- `nexus-core` (runtime/server)
- `nexus-tools-jira`
- `nexus-tools-n8n`
- `nexus-tools-sonarr`
- `nexus-tools-radarr`
- `nexus-tools-tautulli`
- `nexus-tools-starling`

## Monorepo Layout

```text
nexus/
  nexus/                      # nexus-core package
  tool_packs/
    nexus_tools_jira/
    nexus_tools_n8n/
    nexus_tools_sonarr/
    nexus_tools_radarr/
    nexus_tools_tautulli/
    nexus_tools_starling/
```

## Runtime Discovery

Core does not default to `tools`.
Set `NEXUS_TOOL_PACKAGES` to installed pack import roots:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_jira,nexus_tools_n8n"
```

## Bundle

This repo also supports a single-file bundle focused on core runtime files.
See `BUNDLE.md`.
