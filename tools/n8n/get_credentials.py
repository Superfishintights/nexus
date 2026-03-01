"""n8n tool: get_credentials."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve credentials from n8n.",
    examples=["n8n.get_credentials()", 'n8n.get_credentials(limit=50, cursor="abc123")'],
)
def get_credentials(limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve credentials from n8n.

    Args:
        limit: Number of credentials to return (default: 100).
        cursor: Cursor token for pagination.

    Returns:
        The credentials response object.
    """
    client = get_client()
    params: Dict[str, Any] = {"limit": limit}
    if cursor is not None:
        params["cursor"] = cursor
    return client._make_request("credentials", query_params=params)
