"""n8n tool: delete_data_table_rows."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete rows in an n8n data table using a required filter.",
    examples=[
        'n8n.delete_data_table_rows(data_table_id="dt_123", filter="{\\"status\\":\\"archived\\"}")',
        'n8n.delete_data_table_rows(data_table_id="dt_123", filter="{\\"status\\":\\"archived\\"}", return_data=True, dry_run=True)',
    ],
)
def delete_data_table_rows(
    data_table_id: str,
    filter: str,
    return_data: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Delete rows in an n8n data table.

    Args:
        data_table_id: The data table ID.
        filter: JSON string of filter conditions (required).
        return_data: If true, return deleted rows.
        dry_run: If true, preview deletions without deleting rows.

    Returns:
        Delete rows response payload.
    """
    client = get_client()
    params: Dict[str, Any] = {
        "filter": filter,
        "returnData": str(return_data).lower(),
        "dryRun": str(dry_run).lower(),
    }
    return client._make_request(f"data-tables/{data_table_id}/rows/delete", method="DELETE", query_params=params)
