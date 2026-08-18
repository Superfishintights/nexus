"""Start an Audiobookshelf scan for multiple library items."""

from __future__ import annotations

from typing import Any, Sequence

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Start an operational scan for multiple Audiobookshelf library items.",
    examples=['audiobookshelf.batch_scan_items(["item-123", "item-456"])'],
    tool_class="admin",
    aliases=[],
)
def batch_scan_items(item_ids: Sequence[str]) -> Any:
    """POST a batch item scan request to Audiobookshelf."""
    if not item_ids:
        raise ValueError("item_ids must contain at least one item ID")
    if any(not item_id or not item_id.strip() for item_id in item_ids):
        raise ValueError("item_ids must not contain blank item IDs")

    return get_client().post("items/batch/scan", body={"libraryItemIds": list(item_ids)})
