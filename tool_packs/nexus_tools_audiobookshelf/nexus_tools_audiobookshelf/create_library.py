"""Create an Audiobookshelf library."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Create an Audiobookshelf library from a name and folders; optional mediaType, provider, and settings are forwarded.",
    examples=[
        'audiobookshelf.create_library({"name": "Audiobooks", "folders": [{"fullPath": "/media/audiobooks"}]})',
    ],
    tool_class="admin",
    aliases=[],
)
def create_library(library: Dict[str, Any]) -> Any:
    """Validate and POST an Audiobookshelf library definition unchanged."""
    if not isinstance(library, dict) or not library:
        raise ValueError("library must be a non-empty dictionary")

    name = library.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("library must include a non-blank name")

    folders = library.get("folders")
    if not isinstance(folders, list) or not folders:
        raise ValueError("library must include a non-empty folders list")

    for folder in folders:
        if not isinstance(folder, dict):
            raise ValueError("each folder must be a dictionary")
        full_path = folder.get("fullPath")
        if not isinstance(full_path, str) or not full_path.strip():
            raise ValueError("each folder must include a non-blank fullPath")

    return get_client().post("libraries", body=library)
