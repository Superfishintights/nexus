"""n8n tool: get_execution_tags."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Get tags for a specific execution in n8n.",
    examples=["n8n.get_execution_tags(execution_id=123)"],
)
def get_execution_tags(execution_id: int) -> Dict[str, Any]:
    """Get tags for a specific execution in n8n.

    Args:
        execution_id: The ID of the execution.

    Returns:
        Dictionary containing execution tags.
    """
    client = get_client()
    return client._make_request(f"executions/{execution_id}/tags")
