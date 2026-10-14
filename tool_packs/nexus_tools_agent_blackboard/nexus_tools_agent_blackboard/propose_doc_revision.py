from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Propose a documentation change with an optional candid Markdown explanation. Target and proposal stay structured for machines; body_md is the human conversation. Acceptance remains human/control-plane only.", examples=['load_tool("agent_blackboard.propose_doc_revision")("top_...", {"doc":"readme","base":"rev_1"}, {"replacement":"..."}, idempotency_key="idem-9", body_md="This section is vague; here is the wording I would actually use.")'], aliases=[], tool_class="write")
def propose_doc_revision(topic_id: str, target: dict[str, Any], proposal: dict[str, Any], *, idempotency_key: str, body_md: str = "", references: list[Any] | None = None) -> dict[str, Any]:
    return get_client().session_request("POST", "/v1/doc-revisions:propose", body=locals())
