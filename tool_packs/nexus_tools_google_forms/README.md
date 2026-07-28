# nexus_tools_google_forms

Nexus tools for Google Forms API v1.

Install:

```bash
pip install -e .
```

Enable with `NEXUS_TOOL_PACKAGES`:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_google_common,nexus_tools_google_forms"
```

Authentication is provided by `nexus-tools-google-common`. Forms operations require Google OAuth tokens with suitable scopes such as:

- `https://www.googleapis.com/auth/forms.body`
- `https://www.googleapis.com/auth/forms.body.readonly`
- `https://www.googleapis.com/auth/forms.responses.readonly`
- `https://www.googleapis.com/auth/drive.file`
