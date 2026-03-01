"""n8n tool: get_workflow_tags."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve tags associated with a specific n8n workflow.",
    examples=["n8n.get_workflow_tags(workflow_id=\"1\")"],
)
def get_workflow_tags(workflow_id: str) -> Dict[str, Any]:
    """Retrieve tags associated with a specific n8n workflow.

    Args:
        workflow_id: The workflow ID.

    Returns:
        Dictionary containing workflow tags.
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}/tags")
