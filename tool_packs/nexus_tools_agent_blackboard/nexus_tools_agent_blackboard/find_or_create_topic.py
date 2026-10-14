from __future__ import annotations

from typing import Any

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(namespace="agent_blackboard", description="Start or continue the active conversation for every request, including target-system read-only work, while allowing agent-discretion reuse: reuse a clear continuation, create for an independent outcome or real fork, and link related topics.", examples=['load_tool("agent_blackboard.find_or_create_topic")("project:demo", "repo:foo/task:bar", "Implement bar", idempotency_key="idem-3", reuse_topic_id="top_open_investigation")'], aliases=[], tool_class="write")
def find_or_create_topic(
    scope_id: str,
    canonical_subject_key: str,
    title: str,
    *,
    idempotency_key: str,
    summary_md: str | None = None,
    force_new: bool = False,
    reuse_topic_id: str | None = None,
    related_topic_ids: list[str] | None = None,
    tags: list[str] | None = None,
    origin: str | None = None,
    resolution_policy: str = "exact_only",
) -> dict[str, Any]:
    body = locals()
    body["summary_md"] = summary_md or ""
    return get_client().session_request("POST", "/v1/topics:resolve", body=body)
