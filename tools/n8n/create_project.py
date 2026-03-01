"""n8n tool: create_project."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Create a project in n8n.",
    examples=['n8n.create_project(name="Marketing Team")'],
)
def create_project(name: str) -> Dict[str, Any]:
    """Create a project in n8n.

    Args:
        name: The project name.

    Returns:
        The created project payload.
    """
    client = get_client()
    payload = {"name": name}
    return client._make_request("projects", method="POST", data=payload)
