"""List executions from n8n."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Retrieve a list of executions from n8n.",
    examples=["n8n.get_executions(limit=10)", "n8n.get_executions(status=\"error\")"],
)
def get_executions(
    limit: int = 20,
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve a list of executions from n8n.

    Args:
        limit: Number of executions to return.
        status: Filter by status (e.g., error, success, running).
        workflow_id: Filter by workflow ID.

    Returns:
        List of execution summaries.
    """
    client = get_client()
    
    params = {"limit": limit}
    if status:
        params["status"] = status
    if workflow_id:
        params["workflowId"] = workflow_id

    response = client._make_request("executions", query_params=params)
    return response.get("data", [])
