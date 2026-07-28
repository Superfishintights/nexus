# nexus_tools_google_script

Nexus tools for the Google Apps Script API.

Namespace: `google_script`

The pack uses the shared `nexus-tools-google-common` client. Configure OAuth in
the common Google tool settings/environment, including scopes required by the
Apps Script API operation being called.

Common scopes include:

- `https://www.googleapis.com/auth/script.projects`
- `https://www.googleapis.com/auth/script.projects.readonly`
- `https://www.googleapis.com/auth/script.deployments`
- `https://www.googleapis.com/auth/script.deployments.readonly`
- `https://www.googleapis.com/auth/script.processes`
- `https://www.googleapis.com/auth/script.metrics`
