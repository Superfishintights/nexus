"""n8n tool: get_variables."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve variables from n8n.",
    examples=["n8n.get_variables()", 'n8n.get_variables(limit=50, cursor="abc123")'],
)
def get_variables(
    limit: int = 100,
    cursor: Optional[str] = None,
    project_id: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve variables from n8n.

    Args:
        limit: Number of variables to return (default: 100).
        cursor: Cursor token for pagination.
        project_id: Optional project ID filter.
        state: Optional variable state filter.

    Returns:
        The variables response object.
    """
    client = get_client()
    params: Dict[str, Any] = {"limit": limit}
    if cursor is not None:
        params["cursor"] = cursor
    if project_id is not None:
        params["projectId"] = project_id
    if state is not None:
        params["state"] = state
    return client._make_request("variables", query_params=params)
