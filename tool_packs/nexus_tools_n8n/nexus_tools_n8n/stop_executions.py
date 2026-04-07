"""n8n tool: stop_executions."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Stop multiple executions in n8n with optional filters.",
    examples=[
        'n8n.stop_executions(status="running")',
        'n8n.stop_executions(status="queued", workflow_id="2tUt1wbLX592XDdX")',
    ],
)
def stop_executions(
    *,
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    started_after: Optional[str] = None,
    started_before: Optional[str] = None,
) -> Dict[str, Any]:
    """Stop multiple executions in n8n.

    Args:
        status: Optional execution status filter.
        workflow_id: Optional workflow ID filter.
        started_after: Optional ISO datetime; stop executions started after this time.
        started_before: Optional ISO datetime; stop executions started before this time.

    Returns:
        The bulk stop response object.
    """
    client = get_client()
    payload: Dict[str, Any] = {}
    if status is not None:
        payload["status"] = status
    if workflow_id is not None:
        payload["workflowId"] = workflow_id
    if started_after is not None:
        payload["startedAfter"] = started_after
    if started_before is not None:
        payload["startedBefore"] = started_before

    return client._make_request("executions/stop", method="POST", data=payload)
