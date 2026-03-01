"""n8n tool: delete_variable."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete a variable in n8n by ID.",
    examples=['n8n.delete_variable(variable_id="var_123")'],
)
def delete_variable(variable_id: str) -> Dict[str, Any]:
    """Delete a variable in n8n by ID.

    Args:
        variable_id: The variable ID.

    Returns:
        The delete response object (often empty).
    """
    client = get_client()
    return client._make_request(f"variables/{variable_id}", method="DELETE")
