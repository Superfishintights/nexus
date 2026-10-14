from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Release, complete, block, or abandon an owned fenced work claim.", examples=['load_tool("agent_blackboard.release_work")("wrk_...", "clm_...", idempotency_key="idem-6", disposition="completed")'], aliases=[], tool_class="write")
def release_work(work_id: str, claim_id: str, *, idempotency_key: str, disposition: str = "released", reason: str | None = None, expected_version: int | None = None) -> dict[str, Any]:
    return get_client().session_request("POST", f"/v1/work-items/{work_id}/claims/{claim_id}:release", body={key: value for key, value in locals().items() if key not in {"work_id", "claim_id"}})
