from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Search scoped Agent Blackboard topics.", examples=['load_tool("agent_blackboard.search_topics")("project:demo", query="handoff")'], aliases=[], tool_class="read")
def search_topics(scope_id: str, *, query: str = "", states: list[str] | None = None, tags: list[str] | None = None, origin: str | None = None, cursor: str | None = None, limit: int = 20) -> dict[str, Any]:
    return get_client().session_request("GET", "/v1/topics", params=locals())
