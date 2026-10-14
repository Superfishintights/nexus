"""Update the current user's Audiobookshelf media progress."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Update the current user's listening progress for a library item or podcast episode.",
    examples=[
        'audiobookshelf.update_media_progress("item-123", {"currentTime": 120, "isFinished": false})',
        'audiobookshelf.update_media_progress("item-123", {"currentTime": 60}, episode_id="episode-456")',
    ],
    tool_class="write",
    aliases=[],
)
def update_media_progress(
    item_id: str, progress: Dict[str, Any], episode_id: Optional[str] = None
) -> Any:
    """PATCH the current user's exact progress payload for one item or episode."""
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError("item_id must be a non-blank string")
    if not isinstance(progress, dict) or not progress:
        raise ValueError("progress must be a non-empty dictionary")

    client = get_client()
    encoded_item_id = client.segment(item_id, name="item_id")
    path = f"me/progress/{encoded_item_id}"
    if episode_id is not None:
        encoded_episode_id = client.segment(episode_id, name="episode_id")
        path = f"{path}/{encoded_episode_id}"
    return client.patch(path, body=progress)
