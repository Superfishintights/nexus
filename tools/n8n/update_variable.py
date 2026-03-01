"""n8n tool: update_variable."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Update a variable in n8n by ID.",
    examples=['n8n.update_variable(variable_id="var_123", key="API_KEY", value="new-secret")'],
)
def update_variable(
    variable_id: str,
    key: str,
    value: str,
    *,
    variable_type: Optional[str] = None,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a variable in n8n by ID.

    Args:
        variable_id: The variable ID.
        key: Variable key.
        value: Variable value.
        variable_type: Optional variable type.
        project_id: Optional project ID to scope the variable.

    Returns:
        The update response object (often empty).
    """
    client = get_client()
    payload: Dict[str, Any] = {"key": key, "value": value}
    if variable_type is not None:
        payload["type"] = variable_type
    if project_id is not None:
        payload["projectId"] = project_id
    return client._make_request(f"variables/{variable_id}", method="PUT", data=payload)
