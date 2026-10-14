"""Delete multiple Audiobookshelf library items."""

from __future__ import annotations

from typing import Any, Sequence

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Delete selected Audiobookshelf library items in one batch: by default this "
        "removes database entries only; set hard_delete=True to also permanently "
        "delete their filesystem media."
    ),
    examples=[
        'audiobookshelf.batch_delete_items(["item-123", "item-456"])',
        'audiobookshelf.batch_delete_items(["item-123"], hard_delete=True)',
    ],
    tool_class="destructive",
    aliases=[],
)
def batch_delete_items(item_ids: Sequence[str], hard_delete: bool = False) -> Any:
    """Delete non-empty item IDs, optionally removing their media files as well."""
    if not item_ids:
        raise ValueError("item_ids must contain at least one item ID")
    if any(not item_id or not item_id.strip() for item_id in item_ids):
        raise ValueError("item_ids must not contain blank item IDs")

    return get_client().post(
        "items/batch/delete",
        body={"libraryItemIds": list(item_ids)},
        params={"hard": 1 if hard_delete else 0},
    )
