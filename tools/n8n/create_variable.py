"""n8n tool: create_variable."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Create a variable in n8n.",
    examples=['n8n.create_variable(key="API_KEY", value="secret")'],
)
def create_variable(
    key: str,
    value: str,
    *,
    variable_type: Optional[str] = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a variable in n8n.

    Args:
        key: Variable key.
        value: Variable value.
        variable_type: Optional variable type.
        project_id: Optional project ID to scope the variable.

    Returns:
        The created variable object.
    """
    client = get_client()
    payload: Dict[str, Any] = {"key": key, "value": value}
    if variable_type is not None:
        payload["type"] = variable_type
    if project_id is not None:
        payload["projectId"] = project_id
    return client._make_request("variables", method="POST", data=payload)
