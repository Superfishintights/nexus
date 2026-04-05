"""n8n tool: delete_user."""
from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client

@register_tool(
    namespace="n8n",
    description="Delete a user in n8n by ID.",
    examples=['n8n.delete_user(user_id="user_123")'],
)
def delete_user(user_id: str) -> Dict[str, Any]:
    """Delete a user in n8n by ID.

    Args:
        user_id: The user ID.

    Returns:
        The delete response payload (often empty).
    """
    client = get_client()
    return client._make_request(f"users/{user_id}", method="DELETE")
