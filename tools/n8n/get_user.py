"""n8n tool: get_user."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Retrieve a user from n8n by ID.",
    examples=['n8n.get_user(user_id="user_123")', 'n8n.get_user(user_id="user_123", include_role=True)'],
)
def get_user(user_id: str, include_role: bool = False) -> Dict[str, Any]:
    """Retrieve a user from n8n by ID.

    Args:
        user_id: The user ID.
        include_role: Include role information in the response.

    Returns:
        The user payload.
    """
    client = get_client()
    params = {"includeRole": str(include_role).lower()}
    return client._make_request(f"users/{user_id}", query_params=params)
