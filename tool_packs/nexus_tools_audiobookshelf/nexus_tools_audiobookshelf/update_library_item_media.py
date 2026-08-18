"""Update Audiobookshelf library-item media."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Update an Audiobookshelf library item's book or podcast media metadata and tags "
        "with the official item-media payload, including metadata fields and tags."
    ),
    examples=[
        'audiobookshelf.update_library_item_media("item-123", {"metadata": {"title": "The Sandman", "authors": [{"name": "Neil Gaiman"}]}, "tags": ["fantasy"]})',
    ],
    tool_class="write",
    aliases=[],
)
def update_library_item_media(item_id: str, media_payload: Dict[str, Any]) -> Any:
    """PATCH /api/items/{item_id}/media with an official book or podcast media payload."""
    if not isinstance(media_payload, dict) or not media_payload:
        raise ValueError("media_payload must be a non-empty dictionary")

    client = get_client()
    encoded = client.segment(item_id, name="item_id")
    return client.patch(f"items/{encoded}/media", body=media_payload)
