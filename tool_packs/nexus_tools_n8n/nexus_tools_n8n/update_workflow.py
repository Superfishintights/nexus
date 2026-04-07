"""Update an existing workflow in n8n."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Update an existing workflow in n8n.",
    examples=["n8n.update_workflow(workflow_id=\"1\", name=\"Updated Name\")"],
)
def update_workflow(
    workflow_id: str,
    name: Optional[str] = None,
    nodes: Optional[List[Dict[str, Any]]] = None,
    connections: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
    active: Optional[bool] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Update an existing workflow in n8n.

    Args:
        workflow_id: ID of the workflow to update.
        name: New name of the workflow.
        nodes: List of node objects.
        connections: Dictionary of connections.
        settings: Workflow settings object.
        active: Whether the workflow should be active.
        tags: List of tag IDs.

    Returns:
        The updated workflow object.
    """
    client = get_client()
    
    current = client._make_request(f"workflows/{workflow_id}")
    
    payload = {
        "name": name if name is not None else current.get("name"),
        "nodes": nodes if nodes is not None else current.get("nodes", []),
        "connections": connections if connections is not None else current.get("connections", {}),
        "settings": settings if settings is not None else current.get("settings", {}),
        "active": active if active is not None else current.get("active", False),
        "tags": tags if tags is not None else current.get("tags", []),
    }

    return client._make_request(f"workflows/{workflow_id}", method="PUT", data=payload)
