"""Remove an Audiobookshelf library item's custom cover image."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Permanently remove the custom cover image from an Audiobookshelf library item.",
    examples=[
        'audiobookshelf.remove_library_item_cover("item-id")',
    ],
    tool_class="destructive",
    aliases=[],
)
def remove_library_item_cover(item_id: str) -> Any:
    """DELETE /api/items/{item_id}/cover to remove the item's custom cover image."""
    client = get_client()
    return client.delete(f"items/{client.segment(item_id, name='item_id')}/cover")
