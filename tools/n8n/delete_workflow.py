"""Delete a workflow from n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Delete a workflow from n8n.",
    examples=["n8n.delete_workflow(\"1\")"],
)
def delete_workflow(workflow_id: str) -> Dict[str, Any]:
    """Delete a workflow from n8n.

    Args:
        workflow_id: The ID of the workflow to delete.

    Returns:
        The deleted workflow object (or success message).
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}", method="DELETE")
