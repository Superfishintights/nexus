# nexus_tools_google_slides

Nexus tools for Google Slides API v1.

Install:

```bash
pip install -e .
```

Enable with `NEXUS_TOOL_PACKAGES`:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_google_slides"
```

This pack depends on `nexus-tools-google-common>=0.1.0` for OAuth/token handling.
It uses the official Google Slides REST v1 endpoint and keeps all tool metadata
literal for Nexus catalog scanning.

Reference: https://developers.google.com/workspace/slides/api/reference/rest
