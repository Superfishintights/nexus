"""Retrieve an Audiobookshelf series by ID."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Retrieve an Audiobookshelf series by ID.",
    examples=['audiobookshelf.get_series("series-123", {"include": "books"})'],
    tool_class="read",
    aliases=[],
)
def get_series(series_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Retrieve an Audiobookshelf series by ID."""
    client = get_client()
    encoded = client.segment(series_id, name="series_id")
    return client.get(f"series/{encoded}", params=params)
