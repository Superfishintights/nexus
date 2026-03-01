"""n8n tool: stop_execution."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Stop a running execution in n8n.",
    examples=["n8n.stop_execution(execution_id=123)"],
)
def stop_execution(execution_id: int) -> Dict[str, Any]:
    """Stop a running execution in n8n.

    Args:
        execution_id: The ID of the execution to stop.

    Returns:
        The stop response object.
    """
    client = get_client()
    return client._make_request(f"executions/{execution_id}/stop", method="POST")
