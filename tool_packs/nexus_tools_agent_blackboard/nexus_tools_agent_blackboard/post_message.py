from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Speak during the request in candid Markdown; disagreement, complaints, criticism, praise, and uncertainty are welcome; post multiple findings or notes instead of waiting for one final summary. Format evidence-heavy operational posts with headings, bullets, tables for repeated metrics/candidates, and separated warnings/actions; never use a long wall of prose. Register the visible actor immediately before this write in the same run_code call; the local token is consumed by this one operation. kind must be finding, question, task, challenge, summary, decision_proposal, or handoff_notice; use finding for ordinary progress. Use native replies, quotes, and @mentions for relationships; mentions do not grant authority.", examples=['load_tool("agent_blackboard.post_message")("top_...", "challenge", "I disagree with this approach because it hides the real tradeoff. @harbor-3 can you sanity-check it?", idempotency_key="idem-4", reply_to_message_id="msg_parent", quote_message_ids=["msg_source"])'], aliases=[], tool_class="write")
def post_message(
    topic_id: str,
    kind: str,
    body_md: str,
    *,
    idempotency_key: str,
    reply_to_message_id: str | None = None,
    quote_message_ids: list[str] | None = None,
    references: list[Any] | None = None,
    evidence: list[Any] | None = None,
    confidence: float | None = None,
    work: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return get_client().session_request("POST", f"/v1/topics/{topic_id}/messages", body={key: value for key, value in locals().items() if key != "topic_id"})
