"""n8n tool: update_workflow_tags."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update tags for a specific n8n workflow.",
    examples=["n8n.update_workflow_tags(workflow_id=\"1\", tag_ids=[\"tag-1\", \"tag-2\"])"],
)
def update_workflow_tags(workflow_id: str, tag_ids: List[str]) -> Dict[str, Any]:
    """Update tags for a specific n8n workflow.

    Args:
        workflow_id: The workflow ID.
        tag_ids: List of tag IDs to assign to the workflow.

    Returns:
        Dictionary containing the updated workflow tags.
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}/tags", method="PUT", data=tag_ids)
