"""n8n tool: change_project_user_role."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Change a user's role inside an n8n project.",
    examples=[
        (
            'n8n.change_project_user_role(project_id="proj_123", '
            'user_id="user_456", role="project:admin")'
        )
    ],
)
def change_project_user_role(project_id: str, user_id: str, role: str) -> Dict[str, Any]:
    """Change a user's role inside an n8n project.

    Args:
        project_id: The project ID.
        user_id: The user ID.
        role: The role to set.

    Returns:
        The role change response payload.
    """
    client = get_client()
    payload = {"role": role}
    return client._make_request(
        f"projects/{project_id}/users/{user_id}",
        method="PATCH",
        data=payload,
    )
