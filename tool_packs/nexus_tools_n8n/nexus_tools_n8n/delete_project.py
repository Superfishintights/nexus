"""n8n tool: delete_project."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete a project in n8n by ID.",
    examples=['n8n.delete_project(project_id="proj_123")'],
)
def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete a project in n8n by ID.

    Args:
        project_id: The project ID.

    Returns:
        The delete response payload (often empty).
    """
    client = get_client()
    return client._make_request(f"projects/{project_id}", method="DELETE")
