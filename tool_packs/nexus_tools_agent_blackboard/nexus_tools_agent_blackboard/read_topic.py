from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Read topic synopsis, messages, work, claims, handoffs, artifacts, and provenance.", examples=['load_tool("agent_blackboard.read_topic")("top_...")'], aliases=[], tool_class="read")
def read_topic(topic_id: str, *, cursor: str | None = None, limit: int = 50, include_synopsis: bool = True, kinds: list[str] | None = None) -> dict[str, Any]:
    return get_client().session_request("GET", f"/v1/topics/{topic_id}", params=locals())
