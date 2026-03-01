"""n8n tool: upsert_data_table_row."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Upsert a row in an n8n data table using a filter.",
    examples=[
        'n8n.upsert_data_table_row(data_table_id="dt_123", filter="{\\"email\\":\\"a@example.com\\"}", data={"email":"a@example.com","name":"Alice"})',
    ],
)
def upsert_data_table_row(
    data_table_id: str,
    filter: str,
    data: Dict[str, Any],
    return_data: Optional[bool] = None,
    dry_run: Optional[bool] = None,
) -> Dict[str, Any]:
    """Upsert a row in an n8n data table.

    Args:
        data_table_id: The data table ID.
        filter: JSON string of filter conditions.
        data: Row values used for update/insert.
        return_data: If true, return the upserted row.
        dry_run: If true, preview upsert without applying changes.

    Returns:
        Upsert response payload.
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

    return client._make_request(f"data-tables/{data_table_id}/rows/upsert", method="POST", data=payload)
