"""Retry an execution in n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Retry an execution in n8n.",
    examples=["n8n.retry_execution(\"123\")"],
)
def retry_execution(execution_id: str) -> Dict[str, Any]:
    """Retry an execution in n8n.

    Args:
        execution_id: The ID of the execution to retry.

    Returns:
        The new execution object.
    """
    client = get_client()
    return client._make_request(f"executions/{execution_id}/retry", method="POST")
