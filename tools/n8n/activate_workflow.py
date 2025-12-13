"""Activate a workflow in n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Activate a workflow in n8n.",
    examples=["n8n.activate_workflow(\"1\")"],
)
def activate_workflow(workflow_id: str) -> Dict[str, Any]:
    """Activate a workflow in n8n.

    Args:
        workflow_id: The ID of the workflow to activate.

    Returns:
        The updated workflow object.
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}/activate", method="POST")
