"""Fetch multiple Audiobookshelf library items in one request."""

from __future__ import annotations

from typing import Any, Sequence

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Get selected Audiobookshelf library items in a single batch request.",
    examples=['audiobookshelf.batch_get_items(["item-123", "item-456"])'],
    tool_class="read",
    aliases=[],
)
def batch_get_items(item_ids: Sequence[str]) -> Any:
    """Fetch a non-empty set of non-blank Audiobookshelf library item IDs."""
    if isinstance(item_ids, (str, bytes)) or not item_ids:
        raise ValueError("item_ids must be a non-empty sequence of non-empty strings")

    library_item_ids = list(item_ids)
    if any(
        not isinstance(item_id, str) or not item_id.strip()
        for item_id in library_item_ids
    ):
        raise ValueError("item_ids must contain only non-empty strings")

    return get_client().post("items/batch/get", body={"libraryItemIds": library_item_ids})
