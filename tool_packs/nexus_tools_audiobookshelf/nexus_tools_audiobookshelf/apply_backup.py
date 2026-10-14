"""Apply an Audiobookshelf server backup."""

from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description=(
        "Apply an Audiobookshelf server backup. This restores server data and restarts "
        "the server, interrupting active service."
    ),
    examples=['audiobookshelf.apply_backup("backup-123")'],
    tool_class="destructive",
    aliases=[],
)
def apply_backup(backup_id: str) -> Any:
    """Apply the backup through Audiobookshelf's mutating GET endpoint."""
    client = get_client()
    encoded = client.segment(backup_id, name="backup_id")
    return client.get(f"backups/{encoded}/apply")
