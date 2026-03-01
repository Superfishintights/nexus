"""n8n tool: get_data_table."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Get a data table from n8n by ID.",
    examples=['n8n.get_data_table(data_table_id="dt_123")'],
)
def get_data_table(data_table_id: str) -> Dict[str, Any]:
    """Get a data table from n8n by ID.

    Args:
        data_table_id: The data table ID.

    Returns:
        Data table payload.
    """
    client = get_client()
    return client._make_request(f"data-tables/{data_table_id}")
