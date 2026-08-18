"""Google Forms form resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import forms_request, merge_params, quote_path_segment, require_array, require_object


def _write_control(required_revision_id: Optional[str], target_revision_id: Optional[str]) -> Optional[Dict[str, str]]:
    if required_revision_id and target_revision_id:
        raise ValueError("Use either required_revision_id or target_revision_id, not both")
    if required_revision_id:
        return {"requiredRevisionId": required_revision_id}
    if target_revision_id:
        return {"targetRevisionId": target_revision_id}
    return None


@register_tool(
    namespace="google_forms",
    description="Create a Google Form with title and optional document title.",
    examples=['load_tool("google_forms.create_form")("Customer survey", document_title="Q3 customer survey")'],
    aliases=[],
    tool_class="write",
)
def create_form(title: str, *, document_title: Optional[str] = None, unpublished: Optional[bool] = None) -> Dict[str, Any]:
    info = {"title": title}
    if document_title:
        info["documentTitle"] = document_title
    return forms_request("POST", "forms", params={"unpublished": unpublished}, body={"info": info})


@register_tool(
    namespace="google_forms",
    description="Get a Google Form by form ID.",
    examples=['load_tool("google_forms.get_form")("FORM_ID")'],
    aliases=[],
    tool_class="read",
)
def get_form(form_id: str) -> Dict[str, Any]:
    return forms_request("GET", f"forms/{quote_path_segment(form_id)}")


@register_tool(
    namespace="google_forms",
    description="Apply a batch of Google Forms update requests with optional write control.",
    examples=['load_tool("google_forms.batch_update_form")("FORM_ID", [{"updateFormInfo": {"info": {"description": "Updated"}, "updateMask": "description"}}])'],
    aliases=[],
    tool_class="write",
)
def batch_update_form(
    form_id: str,
    requests: list[Dict[str, Any]],
    *,
    include_form_in_response: Optional[bool] = None,
    required_revision_id: Optional[str] = None,
    target_revision_id: Optional[str] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"requests": require_array(requests, "requests")}
    if include_form_in_response is not None:
        body["includeFormInResponse"] = include_form_in_response
    write_control = _write_control(required_revision_id, target_revision_id)
    if write_control:
        body["writeControl"] = write_control
    return forms_request("POST", f"forms/{quote_path_segment(form_id)}:batchUpdate", body=body)


@register_tool(
    namespace="google_forms",
    description="Update publish settings for a Google Form.",
    examples=['load_tool("google_forms.set_publish_settings")("FORM_ID", publish_state={"isPublished": True, "isAcceptingResponses": True})'],
    aliases=[],
    tool_class="write",
)
def set_publish_settings(
    form_id: str,
    *,
    publish_state: Optional[Dict[str, Any]] = None,
    accept_responses: Optional[bool] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = dict(settings or {})
    if publish_state is not None:
        payload["publishState"] = require_object(publish_state, "publish_state")
    elif accept_responses is not None:
        payload["publishState"] = {"isPublished": True, "isAcceptingResponses": accept_responses}
    if not payload:
        raise ValueError("Provide publish_state, accept_responses, or settings")
    return forms_request("POST", f"forms/{quote_path_segment(form_id)}:setPublishSettings", body=payload)


@register_tool(
    namespace="google_forms",
    description="Send a raw request to the Google Forms API v1 for advanced or newly released endpoints.",
    examples=['load_tool("google_forms.request")("GET", "forms/FORM_ID")'],
    aliases=[],
    tool_class="admin",
)
def request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Any] = None,
) -> Any:
    return forms_request(method, path, params=merge_params(params), body=body)
