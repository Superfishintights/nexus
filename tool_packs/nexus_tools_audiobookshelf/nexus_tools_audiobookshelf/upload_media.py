"""Upload media files into an Audiobookshelf library folder."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Upload media files to an Audiobookshelf library folder.",
    examples=[
        'load_tool("audiobookshelf.upload_media")(title="Example Book", library_id="library-id", folder_id="folder-id", file_paths=["/uploads/example.m4b"])',
    ],
    tool_class="write",
    aliases=[],
)
def upload_media(
    title: str,
    library_id: str,
    folder_id: str,
    file_paths: Sequence[str],
    author: Optional[str] = None,
    series: Optional[str] = None,
) -> Any:
    """Upload media using the shared client, which validates paths and multipart data."""
    if not title or not title.strip():
        raise ValueError("title must be non-empty")
    if not library_id or not library_id.strip():
        raise ValueError("library_id must be non-empty")
    if not folder_id or not folder_id.strip():
        raise ValueError("folder_id must be non-empty")
    if not file_paths:
        raise ValueError("file_paths must contain at least one path")

    return get_client().upload_media(
        title=title,
        library_id=library_id,
        folder_id=folder_id,
        file_paths=file_paths,
        author=author,
        series=series,
    )
