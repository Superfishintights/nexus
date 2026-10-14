from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Link a digest/reference-only artifact to a topic; the gateway does not fetch or execute artifacts in MVP.", examples=['load_tool("agent_blackboard.link_artifact")("top_...", {"uri":"https://example.com/a.txt","sha256":"..."}, idempotency_key="idem-8")'], aliases=[], tool_class="write")
def link_artifact(topic_id: str, artifact: dict[str, Any] | str, *, idempotency_key: str, message_id: str | None = None, work_id: str | None = None, relation: str = "supports") -> dict[str, Any]:
    return get_client().session_request("POST", f"/v1/topics/{topic_id}/artifacts", body={key: value for key, value in locals().items() if key != "topic_id"})
