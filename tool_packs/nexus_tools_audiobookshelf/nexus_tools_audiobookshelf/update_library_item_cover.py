"""Select an existing server-side cover image for an Audiobookshelf item."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Set a library item's cover from an existing server-side image path.",
    examples=[
        "audiobookshelf.update_library_item_cover('item-id', '/metadata/covers/item.jpg')",
    ],
    tool_class="write",
    aliases=[],
)
def update_library_item_cover(item_id: str, server_cover_path: str) -> Any:
    """PATCH an item cover selection; this does not upload a client-side file."""
    if not item_id or not item_id.strip():
        raise ValueError("item_id must be non-empty")
    if not server_cover_path or not server_cover_path.strip():
        raise ValueError("server_cover_path must be non-empty")

    client = get_client()
    return client.patch(
        f"items/{client.segment(item_id, name='item_id')}/cover",
        body={"cover": server_cover_path},
    )
