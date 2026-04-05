"""n8n tool: delete_execution."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete an execution from n8n.",
    examples=["n8n.delete_execution(execution_id=123)"],
)
def delete_execution(execution_id: int) -> Dict[str, Any]:
    """Delete an execution from n8n.

    Args:
        execution_id: The ID of the execution to delete.

    Returns:
        The delete response object.
    """
    client = get_client()
    return client._make_request(f"executions/{execution_id}", method="DELETE")
