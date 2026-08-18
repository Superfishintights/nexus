"""Match or rematch an Audiobookshelf library item."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Match or rematch an Audiobookshelf library item with a provider and options.",
    examples=[
        "audiobookshelf.match_library_item('item-123', {'provider': 'google'})",
    ],
    tool_class="write",
    aliases=[],
)
def match_library_item(item_id: str, options: Optional[Dict[str, Any]] = None) -> Any:
    """POST match options for ``item_id`` to Audiobookshelf."""
    client = get_client()
    return client.post(
        f"items/{client.segment(item_id, name='item_id')}/match",
        body=options or {},
    )
