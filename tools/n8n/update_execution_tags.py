"""n8n tool: update_execution_tags."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update tags for a specific execution in n8n.",
    examples=['n8n.update_execution_tags(execution_id=123, tag_ids=["tag-1", "tag-2"])'],
)
def update_execution_tags(execution_id: int, tag_ids: List[str]) -> Dict[str, Any]:
    """Update tags for a specific execution in n8n.

    Args:
        execution_id: The ID of the execution.
        tag_ids: List of tag IDs to assign.

    Returns:
        Dictionary containing updated execution tags.
    """
    client = get_client()
    return client._make_request(f"executions/{execution_id}/tags", method="PUT", data=tag_ids)
