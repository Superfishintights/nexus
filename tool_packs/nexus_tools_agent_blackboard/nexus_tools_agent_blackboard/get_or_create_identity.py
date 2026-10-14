from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="agent_blackboard",
    description="Get or create an Agent Blackboard identity using the local bootstrap credential file.",
    examples=['load_tool("agent_blackboard.get_or_create_identity")("project:demo", "codex:lead", "Codex Lead", idempotency_key="idem-1")'],
    aliases=[],
    tool_class="write",
)
def get_or_create_identity(scope_id: str, identity_key: str, display_name: str, *, idempotency_key: str, identity_kind: str = "stable", runtime_family: str | None = None, parent_identity_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return get_client().bootstrap_request("POST", "/v1/identities:get-or-create", body=locals())
