"""List items in an Audiobookshelf library."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "List library items with documented pagination, sort, and filter parameters, "
        "including encoded issues and missing filters; supports minified, collapseseries, "
        "and include options."
    ),
    examples=[
        'audiobookshelf.list_library_items("library-id", {"page": 0, "limit": 50, "minified": True})',
    ],
    tool_class="read",
    aliases=[],
)
def list_library_items(library_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """GET /api/libraries/{library_id}/items."""
    client = get_client()
    return client.get(
        f"libraries/{client.segment(library_id, name='library_id')}/items",
        params=params,
    )
