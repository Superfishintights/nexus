"""Update Audiobookshelf author metadata."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Update metadata for an Audiobookshelf author.",
    examples=[
        'audiobookshelf.update_author("author-123", {"name": "Ursula K. Le Guin"})',
    ],
    tool_class="write",
    aliases=[],
)
def update_author(author_id: str, updates: Dict[str, Any]) -> Any:
    """PATCH metadata updates for an Audiobookshelf author."""
    if not isinstance(updates, dict) or not updates:
        raise ValueError("updates must be a non-empty dictionary")

    client = get_client()
    encoded = client.segment(author_id, name="author_id")
    return client.patch(f"authors/{encoded}", body=updates)
