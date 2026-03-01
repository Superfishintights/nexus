"""n8n tool: get_workflow_version."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve a specific version of an n8n workflow.",
    examples=["n8n.get_workflow_version(workflow_id=\"1\", version_id=\"abc123\")"],
)
def get_workflow_version(workflow_id: str, version_id: str) -> Dict[str, Any]:
    """Retrieve a specific version of an n8n workflow.

    Args:
        workflow_id: The workflow ID.
        version_id: The workflow version ID.

    Returns:
        Dictionary containing the workflow version details.
    """
    client = get_client()
    return client._make_request(f"workflows/{workflow_id}/{version_id}")
