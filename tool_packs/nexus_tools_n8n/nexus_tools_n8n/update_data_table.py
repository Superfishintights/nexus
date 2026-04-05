"""n8n tool: update_data_table."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update a data table name in n8n.",
    examples=['n8n.update_data_table(data_table_id="dt_123", name="customers_v2")'],
)
def update_data_table(data_table_id: str, name: str) -> Dict[str, Any]:
    """Update a data table name in n8n.

    Args:
        data_table_id: The data table ID.
        name: The new data table name.

    Returns:
        Updated data table payload.
    """
    client = get_client()
    payload = {"name": name}
    return client._make_request(f"data-tables/{data_table_id}", method="PATCH", data=payload)
