"""Match every item in an Audiobookshelf library."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Start the mutating match-all operation for every item in an Audiobookshelf library.",
    examples=['audiobookshelf.match_all_library_items("library-123")'],
    tool_class="admin",
    aliases=[],
)
def match_all_library_items(library_id: str) -> Any:
    """Start Audiobookshelf's match-all operation for the specified library."""
    client = get_client()
    encoded = client.segment(library_id, name="library_id")
    return client.get(f"libraries/{encoded}/matchall")
