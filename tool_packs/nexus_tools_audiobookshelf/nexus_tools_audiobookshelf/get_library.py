"""Retrieve an Audiobookshelf library by ID."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Retrieve an Audiobookshelf library by ID.",
    examples=['audiobookshelf.get_library("library-123", {"include": "items"})'],
    tool_class="read",
    aliases=[],
)
def get_library(library_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Retrieve an Audiobookshelf library by ID."""
    client = get_client()
    encoded = client.segment(library_id, name="library_id")
    return client.get(f"libraries/{encoded}", params=params)
