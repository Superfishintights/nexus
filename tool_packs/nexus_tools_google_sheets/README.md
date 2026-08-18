# Nexus Google Sheets Tool Pack

Google Sheets v4 tools for Nexus under the `google_sheets` namespace.

This pack uses the unified Google auth/client contract from
`nexus-tools-google-common>=0.1.0` and keeps all Sheets-specific request
construction local to this package.

## Configuration

Install core, common, and this pack, then include the package in discovery:

```bash
pip install -e ./nexus
pip install -e ./tool_packs/nexus_tools_google_common
pip install -e ./tool_packs/nexus_tools_google_sheets
export NEXUS_TOOL_PACKAGES="nexus_tools_google_sheets"
```

The common Google client is expected to provide OAuth credentials and a
`request(service, path, method=..., params=..., payload=...)` compatible method.
