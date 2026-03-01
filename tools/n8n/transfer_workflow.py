"""n8n tool: transfer_workflow."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Transfer a workflow to another project in n8n.",
    examples=["n8n.transfer_workflow(workflow_id=\"1\", destination_project_id=\"2\")"],
)
def transfer_workflow(workflow_id: str, destination_project_id: str) -> Dict[str, Any]:
    """Transfer a workflow to another project in n8n.

    Args:
        workflow_id: The workflow ID to transfer.
        destination_project_id: The destination project ID.

    Returns:
        Dictionary containing the transfer result.
    """
    client = get_client()
    payload = {"destinationProjectId": destination_project_id}
    return client._make_request(f"workflows/{workflow_id}/transfer", method="PUT", data=payload)
