"""Start an Audiobookshelf server playback session."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Start an Audiobookshelf server playback session for an item, optionally for a "
        "podcast episode. Supply the official session request including deviceInfo and "
        "supportedMimeTypes; this creates the server session and does not output audio."
    ),
    examples=[
        'audiobookshelf.start_playback_session("item-123", {"deviceInfo": {"clientName": "Nexus", "deviceId": "nexus-1"}, "supportedMimeTypes": ["audio/mpeg"]})',
    ],
    tool_class="write",
    aliases=[],
)
def start_playback_session(
    item_id: str,
    session_request: Dict[str, Any],
    episode_id: Optional[str] = None,
) -> Any:
    """POST /api/items/{item_id}/play, optionally targeting a podcast episode."""
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError("item_id must be a non-blank string")
    if not isinstance(session_request, dict) or not session_request:
        raise ValueError("session_request must be a non-empty dictionary")

    client = get_client()
    encoded_item_id = client.segment(item_id, name="item_id")
    if isinstance(episode_id, str) and episode_id.strip():
        encoded_episode_id = client.segment(episode_id, name="episode_id")
        return client.post(
            f"items/{encoded_item_id}/play/{encoded_episode_id}", body=session_request
        )
    return client.post(f"items/{encoded_item_id}/play", body=session_request)
