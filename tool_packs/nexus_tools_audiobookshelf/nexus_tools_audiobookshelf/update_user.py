"""Update an Audiobookshelf user account."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Update an Audiobookshelf user account's state, permissions, library access, or tag access; "
        "the shared client redacts returned credentials."
    ),
    examples=[
        'audiobookshelf.update_user("user-123", {"isActive": false})',
    ],
    tool_class="admin",
    aliases=[],
)
def update_user(user_id: str, updates: Dict[str, Any]) -> Any:
    """PATCH explicit account, permission, library, or tag access updates for one user."""
    if not isinstance(updates, dict) or not updates:
        raise ValueError("updates must be a non-empty dictionary")
    if "permissions" in updates and not isinstance(updates["permissions"], dict):
        raise ValueError("updates.permissions must be a dictionary")

    client = get_client()
    encoded = client.segment(user_id, name="user_id")
    return client.patch(f"users/{encoded}", body=updates)
