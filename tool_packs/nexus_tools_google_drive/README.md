# Nexus Google Drive Tool Pack

Google Drive v3 tools for Nexus under the `google_drive` namespace.

The pack depends on `nexus-tools-google-common>=0.1.0` for OAuth/session handling
and keeps Drive-specific URL construction, media uploads/downloads, and tool
registration in this package.

Examples:

```python
load_tool("google_drive.search_files")(q="name contains 'report'")
load_tool("google_drive.get_file")("file_id")
load_tool("google_drive.share_file")("file_id", role="reader", email_address="person@example.com")
load_tool("google_drive.export_file")("doc_id", mime_type="application/pdf")
```
