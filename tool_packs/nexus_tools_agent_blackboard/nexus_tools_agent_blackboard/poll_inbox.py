from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Poll the actor inbox with an opaque cursor; wait_seconds is capped by the gateway at 5.", examples=['load_tool("agent_blackboard.poll_inbox")("0", limit=20)'], aliases=[], tool_class="read")
def poll_inbox(cursor: str = "0", *, limit: int = 50, wait_seconds: int = 0, event_types: list[str] | None = None) -> dict[str, Any]:
    return get_client().session_request("GET", "/v1/inbox", params=locals())
