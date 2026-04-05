"""n8n tool: change_user_role."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Change a user's role in n8n.",
    examples=['n8n.change_user_role(user_id="user_123", new_role_name="global:admin")'],
)
def change_user_role(user_id: str, new_role_name: str) -> Dict[str, Any]:
    """Change a user's role in n8n.

    Args:
        user_id: The user ID.
        new_role_name: New role name (for example, "global:admin").

    Returns:
        The role change response payload.
    """
    client = get_client()
    payload = {"newRoleName": new_role_name}
    return client._make_request(f"users/{user_id}/role", method="PATCH", data=payload)
