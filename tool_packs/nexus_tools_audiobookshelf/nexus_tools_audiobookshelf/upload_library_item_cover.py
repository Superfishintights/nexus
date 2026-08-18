"""Upload an Audiobookshelf library item's cover image."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Upload a cover image for an existing library item.",
    examples=[
        "audiobookshelf.upload_library_item_cover(item_id='item-123', file_path='/media/covers/book.jpg')",
    ],
    tool_class="write",
    aliases=[],
)
def upload_library_item_cover(item_id: str, file_path: str) -> Any:
    """Upload ``file_path`` as the cover for ``item_id``."""
    if not item_id or not item_id.strip():
        raise ValueError("item_id must be non-empty")
    if not file_path or not file_path.strip():
        raise ValueError("file_path must be non-empty")

    return get_client().upload_cover(item_id, file_path)
