"""Remove missing or invalid entries from an Audiobookshelf library."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Permanently remove missing or invalid library entries reported as issues by Audiobookshelf.",
    examples=['audiobookshelf.remove_library_items_with_issues("library-id")'],
    tool_class="destructive",
    aliases=[],
)
def remove_library_items_with_issues(library_id: str) -> Any:
    """DELETE /api/libraries/{library_id}/issues to remove invalid entries."""
    client = get_client()
    encoded = client.segment(library_id, name="library_id")
    return client.delete(f"libraries/{encoded}/issues")
