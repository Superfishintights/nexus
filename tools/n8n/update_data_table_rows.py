"""n8n tool: update_data_table_rows."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update rows in an n8n data table using a filter.",
    examples=[
        'n8n.update_data_table_rows(data_table_id="dt_123", filter="{\\"status\\":\\"pending\\"}", data={"status":"done"})',
    ],
)
def update_data_table_rows(
    data_table_id: str,
    filter: str,
    data: Dict[str, Any],
    return_data: Optional[bool] = None,
    dry_run: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update rows in an n8n data table.

    Args:
        data_table_id: The data table ID.
        filter: JSON string of filter conditions.
        data: Values to update.
        return_data: If true, return updated rows.
        dry_run: If true, preview updates without applying changes.

    Returns:
        Update response payload.
    """
    client = get_client()
    payload: Dict[str, Any] = {
        "filter": filter,
        "data": data,
    }
    if return_data is not None:
        payload["returnData"] = return_data
    if dry_run is not None:
        payload["dryRun"] = dry_run

    return client._make_request(f"data-tables/{data_table_id}/rows/update", method="PATCH", data=payload)
