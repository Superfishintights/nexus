# Distribution Guide

Nexus now distributes as multiple packages:

- `nexus-core` (runtime/server)
- `nexus-tools-jira`
- `nexus-tools-n8n`
- `nexus-tools-sonarr`
- `nexus-tools-radarr`
- `nexus-tools-tautulli`
- `nexus-tools-starling`
- `nexus-tools-google-common`
- `nexus-tools-google-calendar`
- `nexus-tools-google-docs`
- `nexus-tools-google-drive`
- `nexus-tools-google-forms`
- `nexus-tools-google-gmail`
- `nexus-tools-google-people`
- `nexus-tools-google-script`
- `nexus-tools-google-sheets`
- `nexus-tools-google-slides`
- `nexus-tools-google-tasks`

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
    nexus_tools_google_common/
    nexus_tools_google_calendar/
    nexus_tools_google_docs/
    nexus_tools_google_drive/
    nexus_tools_google_forms/
    nexus_tools_google_gmail/
    nexus_tools_google_people/
    nexus_tools_google_script/
    nexus_tools_google_sheets/
    nexus_tools_google_slides/
    nexus_tools_google_tasks/
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
