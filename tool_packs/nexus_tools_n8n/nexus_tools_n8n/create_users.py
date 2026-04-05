"""n8n tool: create_users."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Create one or more users in n8n.",
    examples=['n8n.create_users(users=[{"email": "user@example.com", "role": "global:member"}])'],
)
def create_users(users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create one or more users in n8n.

    Args:
        users: Array of user objects expected by n8n.

    Returns:
        The create response payload.
    """
    client = get_client()
    return client._make_request("users", method="POST", data=users)
