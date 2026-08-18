"""Google Forms response resource tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import forms_request, quote_path_segment


@register_tool(
    namespace="google_forms",
    description="List responses submitted to a Google Form with timestamp filter and pagination.",
    examples=['load_tool("google_forms.list_responses")("FORM_ID", filter=\'timestamp >= "2026-07-01T00:00:00Z"\')'],
    aliases=[],
    tool_class="read",
)
def list_responses(
    form_id: str,
    *,
    filter: Optional[str] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    return forms_request(
        "GET",
        f"forms/{quote_path_segment(form_id)}/responses",
        params={"filter": filter, "pageSize": page_size, "pageToken": page_token},
    )


@register_tool(
    namespace="google_forms",
    description="List all Google Form responses across pages up to an optional page cap.",
    examples=['load_tool("google_forms.list_all_responses")("FORM_ID", page_size=5000)'],
    aliases=[],
    tool_class="read",
)
def list_all_responses(
    form_id: str,
    *,
    filter: Optional[str] = None,
    page_size: Optional[int] = 5000,
    max_pages: Optional[int] = None,
) -> Dict[str, Any]:
    responses: list[Dict[str, Any]] = []
    page_token: Optional[str] = None
    pages = 0
    while True:
        page = list_responses(form_id, filter=filter, page_size=page_size, page_token=page_token)
        responses.extend(page.get("responses", []))
        pages += 1
        page_token = page.get("nextPageToken")
        if not page_token or (max_pages is not None and pages >= max_pages):
            return {
                "responses": responses,
                "nextPageToken": page_token,
                "pageCount": pages,
                "responseCount": len(responses),
            }


@register_tool(
    namespace="google_forms",
    description="Get one response submitted to a Google Form.",
    examples=['load_tool("google_forms.get_response")("FORM_ID", "RESPONSE_ID")'],
    aliases=[],
    tool_class="read",
)
def get_response(form_id: str, response_id: str) -> Dict[str, Any]:
    return forms_request(
        "GET",
        f"forms/{quote_path_segment(form_id)}/responses/{quote_path_segment(response_id)}",
    )
