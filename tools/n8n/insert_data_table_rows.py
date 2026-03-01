"""n8n tool: insert_data_table_rows."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Insert rows into an n8n data table.",
    examples=[
        'n8n.insert_data_table_rows(data_table_id="dt_123", data=[{"email":"a@example.com"}])',
        'n8n.insert_data_table_rows(data_table_id="dt_123", data=[{"email":"a@example.com"}], return_type="all")',
    ],
)
def insert_data_table_rows(
    data_table_id: str,
    data: List[Dict[str, Any]],
    return_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert rows into an n8n data table.

    Args:
        data_table_id: The data table ID.
        data: Rows to insert.
        return_type: Optional return type (for example, count, id, all).

    Returns:
        Insert response payload.
    """
    client = get_client()
    payload: Dict[str, Any] = {"data": data}
    if return_type is not None:
        payload["returnType"] = return_type

    return client._make_request(f"data-tables/{data_table_id}/rows", method="POST", data=payload)
