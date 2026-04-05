"""n8n tool: generate_audit."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Generate an audit report in n8n.",
    examples=["n8n.generate_audit()", "n8n.generate_audit(additional_options={\"includeExecutionDetails\": True})"],
)
def generate_audit(additional_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate an audit report in n8n.

    Args:
        additional_options: Optional audit endpoint options.

    Returns:
        Audit report payload.
    """
    client = get_client()

    payload: Dict[str, Any] = {}
    if additional_options is not None:
        payload["additionalOptions"] = additional_options

    return client._make_request("audit", method="POST", data=payload)
