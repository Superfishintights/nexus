"""Add a node to an n8n workflow."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Add a node to an n8n workflow.",
    examples=["n8n.add_node(workflow_id=\"1\", node_type=\"n8n-nodes-base.httpRequest\", node_name=\"My Request\")"],
)
def add_node(
    workflow_id: str,
    node_type: str,
    node_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    position: Optional[List[float]] = None,
    connect_to: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a node to an n8n workflow.

    Args:
        workflow_id: The ID of the workflow.
        node_type: The type of node (e.g., n8n-nodes-base.httpRequest).
        node_name: The name of the new node.
        parameters: Node parameters.
        position: [x, y] coordinates. Defaults to [100, 100] offset from last node or [400, 400].
        connect_to: Name of the node to connect FROM.

    Returns:
        The updated workflow object.
    """
    client = get_client()
    
    workflow = client._make_request(f"workflows/{workflow_id}")
    if not isinstance(workflow, dict):
        raise ValueError(f"Workflow {workflow_id} returned an unexpected response shape")

    nodes = list(workflow.get("nodes", []) or [])
    connections = dict(workflow.get("connections", {}) or {})

    if any(existing.get("name") == node_name for existing in nodes if isinstance(existing, dict)):
        raise ValueError(f"Workflow {workflow_id} already contains a node named {node_name!r}")
    
    # Calculate position if not provided
    if not position:
        if nodes:
            last_node = nodes[-1]
            last_pos = last_node.get("position", [0, 0])
            position = [last_pos[0] + 200, last_pos[1]]
        else:
            position = [400, 400]

    new_node = {
        "parameters": parameters or {},
        "name": node_name,
        "type": node_type,
        "typeVersion": 1,
        "position": position,
    }
    
    nodes.append(new_node)
    
    if connect_to:
        if not any(n.get("name") == connect_to for n in nodes if isinstance(n, dict)):
            raise ValueError(
                f"Workflow {workflow_id} does not contain a source node named {connect_to!r}"
            )

        if connect_to not in connections or not isinstance(connections[connect_to], dict):
            connections[connect_to] = {"main": []}

        # Simple connection logic (main output 0 -> main input 0).
        main_outputs = connections[connect_to].setdefault("main", [])
        if not isinstance(main_outputs, list):
            raise ValueError(f"Workflow {workflow_id} has an invalid connection shape for {connect_to!r}")
        if not main_outputs:
            main_outputs.append([])
        if not isinstance(main_outputs[0], list):
            raise ValueError(f"Workflow {workflow_id} has an invalid first output connection list for {connect_to!r}")

        main_outputs[0].append({
            "node": node_name,
            "type": "main",
            "index": 0,
        })

    # Update workflow
    payload = {"nodes": nodes, "connections": connections}

    return client._make_request(f"workflows/{workflow_id}", method="PUT", data=payload)
