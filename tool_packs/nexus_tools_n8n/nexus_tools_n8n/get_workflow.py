"""Get a specific workflow from n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Retrieve details of a specific n8n workflow.",
    examples=["n8n.get_workflow(\"1\")"],
)
def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Retrieve details of a specific n8n workflow.

    Args:
        workflow_id: The ID of the workflow to retrieve.

    Returns:
        Dictionary containing the workflow details.
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}")
