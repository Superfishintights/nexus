"""n8n tool: list_data_tables."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="List data tables from n8n.",
    examples=["n8n.list_data_tables()", 'n8n.list_data_tables(limit=50, filter="{\\"name\\":\\"customers\\"}")'],
)
def list_data_tables(
    limit: int = 100,
    cursor: Optional[str] = None,
    filter: Optional[str] = None,
    sort_by: Optional[str] = None,
) -> Dict[str, Any]:
    """List data tables from n8n.

    Args:
        limit: Number of tables to return (default: 100).
        cursor: Cursor token for pagination.
        filter: JSON string of filter conditions.
        sort_by: Sort format like field:asc or field:desc.

    Returns:
        Data table list response payload.
    """
    client = get_client()
    params: Dict[str, Any] = {"limit": limit}
    if cursor is not None:
        params["cursor"] = cursor
    if filter is not None:
        params["filter"] = filter
    if sort_by is not None:
        params["sortBy"] = sort_by

    return client._make_request("data-tables", query_params=params)
