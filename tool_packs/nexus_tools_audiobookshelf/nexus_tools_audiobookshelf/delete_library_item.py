"""Delete an Audiobookshelf library item."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Delete an Audiobookshelf library item. By default this deletes only the "
        "database item; set hard_delete=True to also permanently delete its media "
        "files from the filesystem."
    ),
    examples=[
        'audiobookshelf.delete_library_item("item-id")  # database only',
        'audiobookshelf.delete_library_item("item-id", hard_delete=True)  # also delete files',
    ],
    tool_class="destructive",
    aliases=[],
)
def delete_library_item(item_id: str, hard_delete: bool = False) -> Any:
    """DELETE /api/items/{item_id}, optionally deleting its filesystem media too."""
    client = get_client()
    encoded = client.segment(item_id, name="item_id")
    return client.delete(f"items/{encoded}", params={"hard": 1 if hard_delete else 0})
