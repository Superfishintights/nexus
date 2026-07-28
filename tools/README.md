# Tools and Tool Packs

Legacy `tools/` content has been split into installable tool-pack packages under `tool_packs/`.
Use the pack import roots in `NEXUS_TOOL_PACKAGES`.

## First-party Tool Packs

- `nexus_tools_jira`
- `nexus_tools_n8n`
- `nexus_tools_sonarr`
- `nexus_tools_radarr`
- `nexus_tools_tautulli`
- `nexus_tools_starling`
- `nexus_tools_google_common` (shared OAuth/HTTP support; no tools)
- `nexus_tools_google_calendar`
- `nexus_tools_google_docs`
- `nexus_tools_google_drive`
- `nexus_tools_google_forms`
- `nexus_tools_google_gmail`
- `nexus_tools_google_people`
- `nexus_tools_google_script`
- `nexus_tools_google_sheets`
- `nexus_tools_google_slides`
- `nexus_tools_google_tasks`

## Install Pattern

Install `nexus-core`, then only the packs you need.

```bash
pip install -e ./nexus
pip install -e ./tool_packs/nexus_tools_n8n
```

Configure discovery:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_n8n"
```

Google Workspace suite example:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_google_calendar,nexus_tools_google_docs,nexus_tools_google_drive,nexus_tools_google_forms,nexus_tools_google_gmail,nexus_tools_google_people,nexus_tools_google_script,nexus_tools_google_sheets,nexus_tools_google_slides,nexus_tools_google_tasks"
```

Or in `.env`:

```text
NEXUS_TOOL_PACKAGES=nexus_tools_n8n
```

## Notes

- In the monorepo, the legacy value `NEXUS_TOOL_PACKAGES=tools` expands to all
  first-party tool packs for backwards compatibility.

- Discovery is AST-based; modules must be syntactically valid Python.
- Keep `@register_tool(...)` metadata literal where possible for scan accuracy.
- Keep service configuration in env vars or `.env`.

See `tools/ADDING_TOOLSETS.md` for generation/conventions.
