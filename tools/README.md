# Jira Tools

This repository includes a lightweight Jira REST v2 client (`tools/client.py`) and
a small example tool (`tools/get_jira_issue_status.py`). At work you can keep
larger Jira/Sourcegraph/etc toolsets in separate packages and have Nexus discover
them lazily.

## Configuration

Jira tools require:

- `JIRA_HOSTNAME`: Jira hostname or URL (e.g., `jira.company.com`)
- `JIRA_PAT`: Personal Access Token for authentication

## Writing Tools

Tools are single Python functions decorated with `@register_tool`. They may call
external services in either read or write mode; Nexus does not restrict network
access in code execution.

Example:

```python
from nexus.tool_registry import register_tool
from tools.client import get_client

@register_tool(
    description="Get current status for a Jira issue",
    examples=["get_issue_status('PROJ-123')"],
)
def get_issue_status(issue_key: str) -> dict:
    client = get_client()
    issue = client._make_request(f"issue/{issue_key}")
    return {
        "key": issue_key,
        "status": issue["fields"]["status"]["name"],
    }
```

## External Tool Packages

Install any additional tool packages on the machine, then set:

```bash
export NEXUS_TOOL_PACKAGES="tools,company_tools,generated_tools"
```

Nexus will scan these packages for `@register_tool` functions and expose them
via `search_tools`/`get_tool` without importing everything up front.

