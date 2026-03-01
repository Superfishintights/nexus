"""n8n tool: update_project."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update a project name in n8n by ID.",
    examples=['n8n.update_project(project_id="proj_123", name="Renamed Project")'],
)
def update_project(project_id: str, name: str) -> Dict[str, Any]:
    """Update a project name in n8n by ID.

    Args:
        project_id: The project ID.
        name: The new project name.

    Returns:
        The updated project payload.
    """
    client = get_client()
    payload = {"name": name}
    return client._make_request(f"projects/{project_id}", method="PUT", data=payload)
