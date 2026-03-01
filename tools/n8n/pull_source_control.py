"""n8n tool: pull_source_control."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Pull source-control changes in n8n.",
    examples=[
        "n8n.pull_source_control()",
        'n8n.pull_source_control(force=True, auto_publish=False, variables={"ENV": "prod"})',
    ],
)
def pull_source_control(
    *,
    force: Optional[bool] = None,
    auto_publish: Optional[bool] = None,
    variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Pull source-control changes in n8n.

    Args:
        force: Whether to force the pull operation.
        auto_publish: Whether to auto-publish pulled workflows.
        variables: Optional variables passed to the pull operation.

    Returns:
        Dictionary containing the source-control pull result.
    """
    client = get_client()

    payload: Dict[str, Any] = {}
    if force is not None:
        payload["force"] = force
    if auto_publish is not None:
        payload["autoPublish"] = auto_publish
    if variables is not None:
        payload["variables"] = variables

    return client._make_request("source-control/pull", method="POST", data=payload)
