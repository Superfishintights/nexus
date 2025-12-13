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
    
    nodes = workflow.get("nodes", [])
    connections = workflow.get("connections", {})
    
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
        # Check if connect_to node exists
        found = False
        for n in nodes:
            if n["name"] == connect_to:
                found = True
                break
        
        if not found:
             # Just add the node without connection if not found (or raise error? tool should probably warn but proceed)
             pass
        else:
            if connect_to not in connections:
                connections[connect_to] = {"main": []}
            
            # Simple connection logic (main output 0 -> main input 0)
            # n8n connection structure: "NodeName": { "main": [ [ { "node": "TargetNode", "type": "main", "index": 0 } ] ] }
            if "main" not in connections[connect_to]:
                connections[connect_to]["main"] = []
                
            # Ensure we have a list for the first output
            if not connections[connect_to]["main"]:
                connections[connect_to]["main"].append([])
            
            connections[connect_to]["main"][0].append({
                "node": node_name,
                "type": "main",
                "index": 0
            })

    # Update workflow
    payload = {
        "nodes": nodes,
        "connections": connections
    }
    
    return client._make_request(f"workflows/{workflow_id}", method="PUT", data=payload)
