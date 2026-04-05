"""n8n tool: create_data_table."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Create a data table in n8n.",
    examples=[
        'n8n.create_data_table(name="customers", columns=[{"name":"email","type":"string"}])',
    ],
)
def create_data_table(name: str, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a data table in n8n.

    Args:
        name: The data table name.
        columns: Column definitions for the table.

    Returns:
        Created data table payload.
    """
    client = get_client()
    payload = {"name": name, "columns": columns}
    return client._make_request("data-tables", method="POST", data=payload)
