"""n8n tool: get_projects."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve projects from n8n.",
    examples=["n8n.get_projects()", 'n8n.get_projects(limit=50, cursor="abc123")'],
)
def get_projects(limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve projects from n8n.

    Args:
        limit: Number of projects to return (default: 100).
        cursor: Cursor token for pagination.

    Returns:
        The projects response payload.
    """
    client = get_client()
    params: Dict[str, Any] = {"limit": limit}
    if cursor is not None:
        params["cursor"] = cursor
    return client._make_request("projects", query_params=params)
