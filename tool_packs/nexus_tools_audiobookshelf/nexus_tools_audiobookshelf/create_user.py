"""Create an Audiobookshelf user."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Create an Audiobookshelf user with type, permissions, library and tag access; "
        "the token in the response is redacted."
    ),
    examples=[
        'audiobookshelf.create_user({"username": "reader", "password": "secret", "type": "user"})',
    ],
    tool_class="admin",
    aliases=[],
)
def create_user(user: Dict[str, Any]) -> Any:
    """Validate and POST an Audiobookshelf user definition unchanged."""
    if not isinstance(user, dict) or not user:
        raise ValueError("user must be a non-empty dictionary")

    username = user.get("username")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("user must include a non-blank username")

    password = user.get("password")
    if not isinstance(password, str) or not password:
        raise ValueError("user must include a non-empty password string")

    if "permissions" in user and not isinstance(user["permissions"], dict):
        raise ValueError("permissions must be a dictionary when supplied")

    return get_client().post("users", body=user)
