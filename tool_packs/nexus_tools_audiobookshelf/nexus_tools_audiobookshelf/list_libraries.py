"""List Audiobookshelf libraries."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="List Audiobookshelf libraries, with optional include or stats query support.",
    examples=[
        'audiobookshelf.list_libraries({"include": "stats"})',
    ],
    tool_class="read",
    aliases=[],
)
def list_libraries(params: Optional[Dict[str, Any]] = None) -> Any:
    """Return libraries, optionally including requested related data or statistics."""
    return get_client().get("libraries", params=params)
