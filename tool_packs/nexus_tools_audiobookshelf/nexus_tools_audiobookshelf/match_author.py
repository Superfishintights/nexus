"""Match or rematch an Audiobookshelf author."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="audiobookshelf",
    description="Match or rematch an Audiobookshelf author with a provider and options.",
    examples=[
        "audiobookshelf.match_author('author-123', {'provider': 'audible'})",
    ],
    tool_class="write",
    aliases=[],
)
def match_author(author_id: str, options: Optional[Dict[str, Any]] = None) -> Any:
    """POST match options for ``author_id`` to Audiobookshelf."""
    client = get_client()
    return client.post(
        f"authors/{client.segment(author_id, name='author_id')}/match",
        body=options or {},
    )
