"""n8n tool: delete_data_table."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete a data table in n8n by ID.",
    examples=['n8n.delete_data_table(data_table_id="dt_123")'],
)
def delete_data_table(data_table_id: str) -> Dict[str, Any]:
    """Delete a data table in n8n by ID.

    Args:
        data_table_id: The data table ID.

    Returns:
        Delete response payload (often empty).
    """
    client = get_client()
    return client._make_request(f"data-tables/{data_table_id}", method="DELETE")
