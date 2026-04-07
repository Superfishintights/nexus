"""n8n tool: add_project_users."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Add users to a project in n8n.",
    examples=[
        (
            'n8n.add_project_users(project_id="proj_123", '
            'relations=[{"userId": "user_1", "role": "project:editor"}])'
        )
    ],
)
def add_project_users(
    project_id: str,
    relations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Add users to a project in n8n.

    Args:
        project_id: The project ID.
        relations: Project-user relation objects.

    Returns:
        The add users response payload.
    """
    client = get_client()
    payload = {"relations": relations}
    return client._make_request(f"projects/{project_id}/users", method="POST", data=payload)
