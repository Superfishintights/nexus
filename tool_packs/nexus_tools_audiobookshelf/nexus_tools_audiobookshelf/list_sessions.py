"""List Audiobookshelf user sessions."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="List Audiobookshelf user sessions and their activity.",
    examples=['audiobookshelf.list_sessions({"include": "user"})'],
    tool_class="admin",
    aliases=[],
)
def list_sessions(params: Optional[Dict[str, Any]] = None) -> Any:
    """Return Audiobookshelf user sessions, optionally filtered by query parameters."""
    if params is not None and not isinstance(params, dict):
        raise ValueError("params must be a dictionary when supplied")

    return get_client().get("sessions", params=params)
