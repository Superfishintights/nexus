"""Upload an Audiobookshelf server backup archive."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Upload an Audiobookshelf server backup archive.",
    examples=[
        "audiobookshelf.upload_backup(file_path='/backups/audiobookshelf-backup.audiobookshelf')",
    ],
    tool_class="admin",
    aliases=[],
)
def upload_backup(file_path: str) -> Any:
    """Upload ``file_path`` using the shared Audiobookshelf client."""
    if not file_path or not file_path.strip():
        raise ValueError("file_path must be non-empty")

    return get_client().upload_backup(file_path)
