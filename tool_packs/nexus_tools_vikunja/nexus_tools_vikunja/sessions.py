"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text
from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid


@register_tool(
    namespace="vikunja",
    description="List sessions. Returns the authenticated user's own active sessions, most recently active first. Never lists other users' sessions; link share tokens are forbidden. The server requires suitable user authentication; the configured API token may be refused. Credential fields are redacted from responses. Query parameters: [{\"name\":\"page\",\"description\":\"1-based page number.\",\"schema\":{\"default\":1,\"description\":\"1-based page number.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"per_page\",\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"schema\":{\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"q\",\"description\":\"Search query; filters the list to items matching this string.\",\"schema\":{\"description\":\"Search query; filters the list to items matching this string.\",\"type\":\"string\"}}]",
    examples=['load_tool("vikunja.list_sessions")()'],
    tool_class='read',
    aliases=[],
)
def list_sessions(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    "GET /api/v2/user/sessions. Returns the authenticated user's own active sessions, most recently active first. Never lists other users' sessions; link share tokens are forbidden."
    client = get_client()
    return safe_response(client.page('user/sessions', page=page, per_page=per_page, params={**(params or {}), **({'q': query} if query is not None else {})}))


@register_tool(
    namespace="vikunja",
    description="Delete a session. Revokes a session by its UUID. Only the owning user may delete it; deleting another user's session is forbidden. The server requires suitable user authentication; the configured API token may be refused. Credential fields are redacted from responses.",
    examples=['load_tool("vikunja.delete_session")(session_id="00000000-0000-4000-8000-000000000001")'],
    tool_class='admin',
    aliases=[],
)
def delete_session(session_id: str, params: dict[str, Any] | None = None) -> Any:
    "DELETE /api/v2/user/sessions/{session}. Revokes a session by its UUID. Only the owning user may delete it; deleting another user's session is forbidden."
    client = get_client()
    return safe_response(safe_request(client, 'DELETE', f'user/sessions/{path_text(session_uuid(session_id))}', params=params))

