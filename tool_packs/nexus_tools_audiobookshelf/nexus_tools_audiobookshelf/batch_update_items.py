"""Batch-update Audiobookshelf library items."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Update the media payload for multiple Audiobookshelf library items in one request.",
    examples=[
        'audiobookshelf.batch_update_items([{"id": "item-123", "mediaPayload": {"metadata": {"title": "The Sandman"}}}])',
    ],
    tool_class="write",
    aliases=[],
)
def batch_update_items(updates: Sequence[Dict[str, Any]]) -> Any:
    """POST validated library-item media updates to the batch update endpoint."""
    if isinstance(updates, (str, bytes)) or not isinstance(updates, Sequence) or not updates:
        raise ValueError("updates must be a non-empty sequence")

    requested_updates = list(updates)
    seen_ids = set()
    for update in requested_updates:
        if not isinstance(update, dict) or not update:
            raise ValueError("each update must be a non-empty dictionary")

        item_id = update.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("each update must include a non-blank id")
        if item_id in seen_ids:
            raise ValueError("updates must not contain duplicate item IDs")
        seen_ids.add(item_id)

        if not isinstance(update.get("mediaPayload"), dict):
            raise ValueError("each update must include a dictionary mediaPayload")

    return get_client().post("items/batch/update", body=requested_updates)
