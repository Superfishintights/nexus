from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Write a natural-language Markdown handoff in your own voice. Optional structured fields help machines resume the work but should not replace an honest narrative summary.", examples=['load_tool("agent_blackboard.post_handoff")("top_...", "I got the gateway working, but the projector still annoys me: retries need proof before I trust it.", idempotency_key="idem-7")'], aliases=[], tool_class="write")
def post_handoff(topic_id: str, summary_md: str, *, idempotency_key: str, work_id: str | None = None, claim_id: str | None = None, state: dict[str, Any] | None = None, attempted: list[str] | None = None, remaining: list[str] | None = None, blockers: list[str] | None = None, references: list[Any] | None = None, target_capabilities: list[str] | None = None, release_claim: bool = False) -> dict[str, Any]:
    return get_client().session_request("POST", f"/v1/topics/{topic_id}/handoffs", body={key: value for key, value in locals().items() if key != "topic_id"})
