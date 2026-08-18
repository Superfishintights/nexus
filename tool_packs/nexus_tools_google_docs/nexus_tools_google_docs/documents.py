"""Google Docs document endpoint tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import (
    clean_body,
    clean_params,
    coerce_json,
    coerce_optional_str,
    docs_request,
    document_path,
    require_request_list,
)


@register_tool(
    namespace="google_docs",
    description="Create a Google Docs document by title.",
    examples=["load_tool('google_docs.create_document')('Project notes')"],
    tool_class="write",
    aliases=[],
)
def create_document(title: str) -> Dict[str, Any]:
    return docs_request("documents", method="POST", payload={"title": title})


@register_tool(
    namespace="google_docs",
    description="Get a Google Docs document structure by document ID.",
    examples=["load_tool('google_docs.get_document')('DOC_ID', fields='title,body/content')"],
    tool_class="read",
    aliases=[],
)
def get_document(
    document_id: str,
    *,
    fields: Optional[str] = None,
    suggestions_view_mode: Optional[str] = None,
    include_tabs_content: Optional[bool] = None,
) -> Dict[str, Any]:
    return docs_request(
        document_path(document_id),
        params=clean_params(
            {
                "fields": coerce_optional_str(fields),
                "suggestionsViewMode": coerce_optional_str(suggestions_view_mode),
                "includeTabsContent": include_tabs_content,
            }
        ),
    )


@register_tool(
    namespace="google_docs",
    description="Apply a raw Google Docs batchUpdate request list.",
    examples=["load_tool('google_docs.batch_update_document')('DOC_ID', [{'insertText': {'location': {'index': 1}, 'text': 'Hello'}}])"],
    tool_class="destructive",
    aliases=[],
)
def batch_update_document(
    document_id: str,
    requests: Any,
    *,
    write_control: Optional[Any] = None,
) -> Dict[str, Any]:
    body = clean_body(
        {
            "requests": require_request_list(requests),
            "writeControl": coerce_json(write_control),
        }
    )
    return docs_request(document_path(document_id, ":batchUpdate"), method="POST", payload=body)
