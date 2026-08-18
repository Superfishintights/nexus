"""Retrieve an Audiobookshelf author by ID."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Retrieve an Audiobookshelf author by ID.",
    examples=['audiobookshelf.get_author("author-123", {"include": "items"})'],
    tool_class="read",
    aliases=[],
)
def get_author(author_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Retrieve an Audiobookshelf author by ID."""
    client = get_client()
    encoded = client.segment(author_id, name="author_id")
    return client.get(f"authors/{encoded}", params=params)
