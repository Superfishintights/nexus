"""Google Forms watch resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import forms_request, quote_path_segment


@register_tool(
    namespace="google_forms",
    description="Create a Google Forms watch that sends schema or response notifications to Cloud Pub/Sub.",
    examples=['load_tool("google_forms.create_watch")("FORM_ID", "RESPONSES", "projects/my-project/topics/forms")'],
    aliases=[],
    tool_class="write",
)
def create_watch(
    form_id: str,
    event_type: str,
    topic_name: str,
    *,
    watch_id: Optional[str] = None,
    watch: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    watch_body = dict(watch or {})
    watch_body.setdefault("eventType", event_type)
    watch_body.setdefault("target", {"topic": {"topicName": topic_name}})
    body: Dict[str, Any] = {"watch": watch_body}
    if watch_id:
        body["watchId"] = watch_id
    return forms_request("POST", f"forms/{quote_path_segment(form_id)}/watches", body=body)


@register_tool(
    namespace="google_forms",
    description="List Google Forms watches owned by the invoking project for one form.",
    examples=['load_tool("google_forms.list_watches")("FORM_ID")'],
    aliases=[],
    tool_class="read",
)
def list_watches(form_id: str) -> Dict[str, Any]:
    return forms_request("GET", f"forms/{quote_path_segment(form_id)}/watches")


@register_tool(
    namespace="google_forms",
    description="Renew a Google Forms watch for another seven days.",
    examples=['load_tool("google_forms.renew_watch")("FORM_ID", "watch-id")'],
    aliases=[],
    tool_class="write",
)
def renew_watch(form_id: str, watch_id: str) -> Dict[str, Any]:
    return forms_request(
        "POST",
        f"forms/{quote_path_segment(form_id)}/watches/{quote_path_segment(watch_id)}:renew",
        body={},
    )


@register_tool(
    namespace="google_forms",
    description="Delete a Google Forms watch.",
    examples=['load_tool("google_forms.delete_watch")("FORM_ID", "watch-id")'],
    aliases=[],
    tool_class="destructive",
)
def delete_watch(form_id: str, watch_id: str) -> Dict[str, Any]:
    return forms_request(
        "DELETE",
        f"forms/{quote_path_segment(form_id)}/watches/{quote_path_segment(watch_id)}",
    )
