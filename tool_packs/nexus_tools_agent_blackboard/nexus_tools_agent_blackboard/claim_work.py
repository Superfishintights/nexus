from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Acquire, renew, or accept a targeted handoff into a fenced work claim.", examples=['load_tool("agent_blackboard.claim_work")("wrk_...", idempotency_key="idem-5")'], aliases=[], tool_class="write")
def claim_work(work_id: str, *, idempotency_key: str, claim_id: str | None = None, handoff_id: str | None = None, lease_seconds: int = 900, expected_version: int | None = None, note: str | None = None) -> dict[str, Any]:
    return get_client().session_request("POST", f"/v1/work-items/{work_id}/claims", body={key: value for key, value in locals().items() if key != "work_id"})
