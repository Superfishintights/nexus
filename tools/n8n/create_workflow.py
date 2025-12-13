"""Create a new workflow in n8n."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Create a new workflow in n8n.",
    examples=["n8n.create_workflow(name=\"My New Workflow\", active=True)"],
)
def create_workflow(
    name: str,
    nodes: Optional[List[Dict[str, Any]]] = None,
    connections: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
    active: bool = False,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new workflow in n8n.

    Args:
        name: Name of the workflow.
        nodes: List of node objects. Defaults to empty list.
        connections: Dictionary of connections. Defaults to empty dict.
        settings: Workflow settings object.
        active: Whether the workflow should be active.
        tags: List of tag IDs or names.

    Returns:
        The created workflow object.
    """
    client = get_client()
    
    payload = {
        "name": name,
        "nodes": nodes or [],
        "connections": connections or {},
        "settings": settings or {},
        "active": active,
    }
    
    if tags:
        payload["tags"] = tags

    return client._make_request("workflows", method="POST", data=payload)
