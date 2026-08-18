"""Batch quick-match Audiobookshelf library items."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Quick-match selected Audiobookshelf library items in a single batch request.",
    examples=[
        "audiobookshelf.batch_quick_match_items(['item-123', 'item-456'], {'provider': 'google'})",
    ],
    tool_class="admin",
    aliases=[],
)
def batch_quick_match_items(
    item_ids: Sequence[str], options: Optional[Dict[str, Any]] = None
) -> Any:
    """Quick-match non-empty item IDs; options support provider and override flags."""
    if isinstance(item_ids, (str, bytes)) or not item_ids:
        raise ValueError("item_ids must be a non-empty sequence of non-empty strings")

    library_item_ids = list(item_ids)
    if any(not isinstance(item_id, str) or not item_id.strip() for item_id in library_item_ids):
        raise ValueError("item_ids must contain only non-empty strings")

    return get_client().post(
        "items/batch/quickmatch",
        body={"libraryItemIds": library_item_ids, "options": options or {}},
    )
