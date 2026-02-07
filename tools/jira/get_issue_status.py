"""Get the current status and available transitions for a Jira issue."""

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="jira",
    aliases=["get_issue_status"],
    description="Get the current status and available transitions for a Jira issue.",
    examples=["jira.get_issue_status('PROJ-123')"],
)
def get_issue_status(issue_key: str) -> Dict[str, Any]:
    """Get the current status and available transitions for a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g., 'PROJ-123')

    Returns:
        Dictionary containing current status and available transitions.
    """
    client = get_client()

    issue_data = client._make_request(f"issue/{issue_key}")
    current_status = issue_data.get("fields", {}).get("status", {})

    transitions_data = client._make_request(f"issue/{issue_key}/transitions")

    available_transitions = []
    for transition in transitions_data.get("transitions", []):
        transition_info = {
            "id": transition.get("id"),
            "name": transition.get("name"),
            "to": {
                "id": transition.get("to", {}).get("id"),
                "name": transition.get("to", {}).get("name"),
                "statusCategory": transition.get("to", {})
                .get("statusCategory", {})
                .get("name"),
            }
            if transition.get("to")
            else None,
        }
        available_transitions.append(transition_info)

    response = {
        "issueKey": issue_key,
        "currentStatus": {
            "id": current_status.get("id"),
            "name": current_status.get("name"),
            "description": current_status.get("description"),
            "statusCategory": {
                "id": current_status.get("statusCategory", {}).get("id"),
                "name": current_status.get("statusCategory", {}).get("name"),
                "key": current_status.get("statusCategory", {}).get("key"),
                "colorName": current_status.get("statusCategory", {}).get("colorName"),
            }
            if current_status.get("statusCategory")
            else None,
        },
        "availableTransitions": available_transitions,
    }

    return response
