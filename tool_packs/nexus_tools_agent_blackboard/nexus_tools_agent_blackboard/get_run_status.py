from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Get the token-bound actor/run state, active claims, capability set, and kill-switch status.", examples=['load_tool("agent_blackboard.get_run_status")()'], aliases=[], tool_class="read")
def get_run_status() -> dict[str, Any]:
    return get_client().session_request("GET", "/v1/runs/current")
