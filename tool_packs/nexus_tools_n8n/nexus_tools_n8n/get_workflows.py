"""List workflows from n8n."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Retrieve a list of workflows from n8n.",
    examples=["n8n.get_workflows(limit=10)", "n8n.get_workflows(active=True)"],
)
def get_workflows(
    limit: int = 20,
    active: Optional[bool] = None,
    tags: Optional[str] = None,
    name: Optional[str] = None,
    project_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve a list of workflows from n8n.

    Args:
        limit: Number of workflows to return (default: 20).
        active: Filter by active status (True/False).
        tags: Filter by tags (comma-separated names or IDs).
        name: Filter by workflow name.
        project_id: Filter by project ID.

    Returns:
        List of workflow summaries.
    """
    client = get_client()
    
    params = {"limit": limit}
    if active is not None:
        params["active"] = str(active).lower()
    if tags:
        params["tags"] = tags
    if name:
        params["name"] = name
    if project_id:
        params["projectId"] = project_id

    response = client._make_request("workflows", query_params=params)
    return response.get("data", [])
