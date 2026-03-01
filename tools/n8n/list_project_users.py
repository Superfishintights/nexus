"""n8n tool: list_project_users."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="List users in an n8n project.",
    examples=[
        'n8n.list_project_users(project_id="proj_123")',
        'n8n.list_project_users(project_id="proj_123", limit=50, cursor="abc123")',
    ],
)
def list_project_users(
    project_id: str,
    limit: int = 100,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """List users in an n8n project.

    Args:
        project_id: The project ID.
        limit: Number of users to return (default: 100).
        cursor: Cursor token for pagination.

    Returns:
        The project users response payload.
    """
    client = get_client()
    params: Dict[str, Any] = {"limit": limit}
    if cursor is not None:
        params["cursor"] = cursor
    return client._make_request(f"projects/{project_id}/users", query_params=params)
