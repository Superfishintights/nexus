"""n8n tool: get_data_table_rows."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Get rows from an n8n data table.",
    examples=[
        'n8n.get_data_table_rows(data_table_id="dt_123", filter="{\\"status\\":\\"active\\"}")',
        'n8n.get_data_table_rows(data_table_id="dt_123", sort_by="createdAt:desc", search="john")',
    ],
)
def get_data_table_rows(
    data_table_id: str,
    limit: int = 100,
    cursor: Optional[str] = None,
    filter: Optional[str] = None,
    sort_by: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Get rows from an n8n data table.

    Args:
        data_table_id: The data table ID.
        limit: Number of rows to return (default: 100).
        cursor: Cursor token for pagination.
        filter: JSON string of filter conditions.
        sort_by: Sort format like columnName:asc or columnName:desc.
        search: Search text across string columns.

    Returns:
        Data table rows response payload.
    """
    client = get_client()
    params: Dict[str, Any] = {"limit": limit}
    if cursor is not None:
        params["cursor"] = cursor
    if filter is not None:
        params["filter"] = filter
    if sort_by is not None:
        params["sortBy"] = sort_by
    if search is not None:
        params["search"] = search

    return client._make_request(f"data-tables/{data_table_id}/rows", query_params=params)
