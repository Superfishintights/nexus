"""Get an Audiobookshelf library item."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Get an Audiobookshelf library item, optionally requesting included or expanded "
        "related data."
    ),
    examples=[
        'audiobookshelf.get_library_item("item-id", {"expanded": True})',
    ],
    tool_class="read",
    aliases=[],
)
def get_library_item(item_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """GET /api/items/{item_id}, with optional include or expanded query parameters."""
    client = get_client()
    return client.get(
        f"items/{client.segment(item_id, name='item_id')}",
        params=params,
    )
