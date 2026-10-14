# nexus_tools_google_gmail

Install with:

```bash
pip install -e ./tool_packs/nexus_tools_google_common
pip install -e ./tool_packs/nexus_tools_google_gmail
```

Then add this package root to `NEXUS_TOOL_PACKAGES`.

The pack uses namespace `google_gmail` and delegates OAuth/config handling to
`nexus_tools_google_common.client`.
