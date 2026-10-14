"""List authors in an Audiobookshelf library."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "List library authors with the current pagination, filter, and sort "
        "parameters supported by Audiobookshelf."
    ),
    examples=[
        'audiobookshelf.list_library_authors("library-id", {"page": 0, "limit": 50, "sort": "name"})',
    ],
    tool_class="read",
    aliases=[],
)
def list_library_authors(library_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """GET /api/libraries/{library_id}/authors."""
    client = get_client()
    return client.get(
        f"libraries/{client.segment(library_id, name='library_id')}/authors",
        params=params,
    )
