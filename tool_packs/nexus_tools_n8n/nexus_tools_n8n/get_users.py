"""n8n tool: get_users."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve users from n8n.",
    examples=["n8n.get_users()", 'n8n.get_users(limit=50, include_role=True, project_id="proj_123")'],
)
def get_users(
    limit: int = 100,
    cursor: Optional[str] = None,
    include_role: bool = False,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve users from n8n.

    Args:
        limit: Number of users to return (default: 100).
        cursor: Cursor token for pagination.
        include_role: Include role information in the response.
        project_id: Optional project ID filter.

    Returns:
        The users response payload.
    """
    client = get_client()
    params: Dict[str, Any] = {
        "limit": limit,
        "includeRole": str(include_role).lower(),
    }
    if cursor is not None:
        params["cursor"] = cursor
    if project_id is not None:
        params["projectId"] = project_id
    return client._make_request("users", query_params=params)
