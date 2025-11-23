# Jira Tools

This package provides a collection of Python functions for interacting with Jira's REST API. Each tool is implemented as a separate module with a single function that can be imported and called directly by model-generated code.

## Overview

The Jira tools package talks to the Jira HTTP API (version 2) and supports the following categories of tasks:

- Reading issue data (details, status, comments, changelogs)
- Searching issues using JQL (Jira Query Language)
- Creating and updating issues
- Managing comments
- Retrieving project and issue type metadata
- Querying issue links and relationships

## Configuration

The tools require two environment variables:

- `JIRA_HOSTNAME`: The Jira instance hostname or URL (e.g., `jira.company.com` or `https://jira.company.com`)
- `JIRA_PAT`: Personal Access Token for authentication

## Tool List

### Read Operations

- `get_issue_raw(issue_key: str) -> Dict[str, Any]`
  - Get complete raw issue data including all fields (standard and custom)
  - Returns the full JSON response from Jira API

- `get_issue_details(issue_key: str) -> Dict[str, Any]`
  - Get cleaned issue details with key fields extracted
  - Returns structured data for summary, status, assignee, reporter, etc.

- `get_issue_comments(issue_key: str) -> Dict[str, Any]`
  - Get all comments for an issue
  - Returns list of comments with author, body, timestamps

- `get_issue_status(issue_key: str) -> Dict[str, Any]`
  - Get current status and available transitions
  - Returns current status details and list of possible transitions

- `get_projects() -> List[Dict[str, Any]]`
  - Get all accessible Jira projects
  - Returns list of projects with key, name, description, lead

### Search Operations

- `search_issues(jql: str, start_at: int = 0, max_results: int = 50, fields: Optional[str] = None) -> Dict[str, Any]`
  - Search for issues using JQL (Jira Query Language)
  - Returns paginated search results with issue summaries

### Write Operations

- `create_issue(project_key: str, summary: str, description: str, issue_type: str, **kwargs) -> Dict[str, Any]`
  - Create a new Jira issue
  - Returns created issue key and id

- `update_issue(issue_key: str, fields: dict) -> Dict[str, Any]`
  - Update fields on an existing issue
  - Returns success status and list of updated fields

- `add_comment(issue_key: str, comment: str, visibility: Optional[dict] = None) -> Dict[str, Any]`
  - Add a comment to an issue
  - Returns created comment id and details

## Common Workflows

### Check if an issue exists and get its status

```python
from tools.jira.get_issue_details import get_issue_details
from tools.jira.get_issue_status import get_issue_status

issue = get_issue_details('PROJ-123')
status = get_issue_status('PROJ-123')
RESULT = {
    'exists': issue is not None,
    'status': status['currentStatus']['name'],
    'assignee': issue['assignee']['displayName'] if issue.get('assignee') else None,
}
```

### Search for open issues and get summaries

```python
from tools.jira.search_issues import search_issues

results = search_issues('project = PROJ AND status = Open', max_results=10)
RESULT = [
    {'key': issue['key'], 'summary': issue['summary']}
    for issue in results['issues']
]
```

### Create an issue and add a comment

```python
from tools.jira.create_issue import create_issue
from tools.jira.add_comment import add_comment

new_issue = create_issue(
    project_key='PROJ',
    summary='New bug report',
    description='Description of the bug',
    issue_type='Bug',
)

comment = add_comment(
    issue_key=new_issue['key'],
    comment='This is a follow-up comment',
)

RESULT = {
    'issue_key': new_issue['key'],
    'comment_id': comment['commentId'],
}
```

## Constraints & Caveats

- **Authentication**: Requires `JIRA_HOSTNAME` and `JIRA_PAT` environment variables
- **API Version**: Uses Jira REST API v2
- **Rate Limits**: Subject to your Jira instance's rate limiting policies
- **Permissions**: All operations respect the authenticated user's permissions
- **Side Effects**: Write operations (create_issue, update_issue, add_comment) modify Jira data

## Example Code Snippet

```python
from tools.jira.get_issue_details import get_issue_details
from tools.jira.get_issue_comments import get_issue_comments
from tools.jira.search_issues import search_issues

# Get details for a specific issue
issue = get_issue_details('PROJ-123')
print(f"Issue: {issue['summary']}")
print(f"Status: {issue['status']['name']}")

# Get all comments
comments = get_issue_comments('PROJ-123')
print(f"Total comments: {comments['totalComments']}")

# Search for issues
results = search_issues('project = PROJ AND assignee = currentUser()', max_results=5)
print(f"Found {results['total']} issues assigned to me")
for issue in results['issues']:
    print(f"  - {issue['key']}: {issue['summary']}")

# Set the final result
RESULT = {
    'issue': issue,
    'comment_count': comments['totalComments'],
    'my_issues_count': results['total'],
}
```
