"""Deactivate a workflow in n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Deactivate a workflow in n8n.",
    examples=["n8n.deactivate_workflow(\"1\")"],
)
def deactivate_workflow(workflow_id: str) -> Dict[str, Any]:
    """Deactivate a workflow in n8n.

    Args:
        workflow_id: The ID of the workflow to deactivate.

    Returns:
        The updated workflow object.
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}/deactivate", method="POST")
