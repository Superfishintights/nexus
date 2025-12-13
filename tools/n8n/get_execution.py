"""Get a specific execution from n8n."""
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="n8n",
    description="Retrieve details of a specific n8n execution.",
    examples=["n8n.get_execution(\"123\")"],
)
def get_execution(execution_id: str) -> Dict[str, Any]:
    """Retrieve details of a specific n8n execution.

    Args:
        execution_id: The ID of the execution to retrieve.

    Returns:
        Dictionary containing the execution details.
    """
    client = get_client()
    return client._make_request(f"executions/{execution_id}")
