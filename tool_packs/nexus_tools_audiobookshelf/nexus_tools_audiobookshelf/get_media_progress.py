"""Retrieve an authenticated user's Audiobookshelf media progress."""

from __future__ import annotations

from typing import Any, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Retrieve the authenticated user's progress for a media item or episode.",
    examples=[
        'audiobookshelf.get_media_progress("item-123")',
        'audiobookshelf.get_media_progress("podcast-123", "episode-456")',
    ],
    tool_class="read",
    aliases=[],
)
def get_media_progress(item_id: str, episode_id: Optional[str] = None) -> Any:
    """GET /api/me/progress/{item_id}, optionally for a specific episode."""
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError("item_id must be non-empty")

    client = get_client()
    path = f"me/progress/{client.segment(item_id, name='item_id')}"
    if isinstance(episode_id, str) and episode_id.strip():
        path = f"{path}/{client.segment(episode_id, name='episode_id')}"
    return client.get(path)
