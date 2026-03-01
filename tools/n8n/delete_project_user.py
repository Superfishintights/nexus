"""n8n tool: delete_project_user."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete a user from a project in n8n.",
    examples=['n8n.delete_project_user(project_id="proj_123", user_id="user_456")'],
)
def delete_project_user(project_id: str, user_id: str) -> Dict[str, Any]:
    """Delete a user from a project in n8n.

    Args:
        project_id: The project ID.
        user_id: The user ID.

    Returns:
        The delete response payload (often empty).
    """
    client = get_client()
    return client._make_request(f"projects/{project_id}/users/{user_id}", method="DELETE")
