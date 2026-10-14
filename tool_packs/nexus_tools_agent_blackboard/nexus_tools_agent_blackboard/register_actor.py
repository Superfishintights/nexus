from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="agent_blackboard",
    description="Register a distinct per-run actor session with parent, status, subscriptions, and a pleasant collision-safe handle; successors must not impersonate completed actors. For ordinary conversation, omit capabilities so the gateway grants agent_reader and agent_contributor; never invent capability names. Shared Nexus clients rotate sessions: register immediately before each session-bound write in the same run_code call; the local token is consumed by that one dependent operation.",
    examples=['load_tool("agent_blackboard.register_actor")("idn_...", "codex", "host-slot", "run-1", idempotency_key="idem-2", preferred_handle="harbor", task="rollout verification", parent_actor_id="act_parent")'],
    aliases=[],
    tool_class="write",
)
def register_actor(
    identity_id: str,
    runtime: str,
    instance_key: str,
    external_run_key: str,
    *,
    idempotency_key: str,
    runtime_version: str | None = None,
    adapter: str = "nexus",
    parent_actor_id: str | None = None,
    preferred_handle: str | None = None,
    task: str | None = None,
    predecessor_actor_id: str | None = None,
    capabilities: list[str] | None = None,
    subscriptions: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = get_client().bootstrap_request("POST", "/v1/actors:register", body=locals())
    token = result.get("session", {}).pop("token", None)
    if token:
        get_client().write_session_token(token)
        result["session"]["token"] = "[written]"
    return result
