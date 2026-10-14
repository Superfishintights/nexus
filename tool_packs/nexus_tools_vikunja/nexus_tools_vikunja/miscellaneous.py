"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text
from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid


@register_tool(
    namespace="vikunja",
    description="Duplicate a project. Deep-copies a project \u2014 its tasks, files, kanban data, assignees, comments, attachments, labels, relations and backgrounds \u2014 into a new project owned by the authenticated user. User/team/link shares are only copied when duplicate_shares is set to true. The user needs read access to the source project, plus write access to the parent project when one is given. The copy is placed under parent_project_id (top level if omitted). Returns the duplicate in duplicated_project. fields accepts parent_project_id and duplicate_shares. Sharing is not copied unless explicitly requested. Request body schema: {\"content\":{\"application/json\":{\"schema\":{\"$ref\":\"#/components/schemas/ProjectDuplicate\"}}},\"required\":true}",
    examples=['load_tool("vikunja.duplicate_project")(project_id=1, fields={"parent_project_id":0,"duplicate_shares":False})'],
    tool_class='write',
    aliases=[],
)
def duplicate_project(project_id: int, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'POST /api/v2/projects/{projectid}/duplicate. Deep-copies a project — its tasks, files, kanban data, assignees, comments, attachments, labels, relations and backgrounds — into a new project owned by the authenticated user. User/team/link shares are only copied when duplicate_shares is set to true. The user needs read access to the source project, plus write access to the parent project when one is given. The copy is placed under parent_project_id (top level if omitted). Returns the duplicate in duplicated_project.'
    client = get_client()
    return safe_response(safe_request(client, 'POST', f'projects/{positive_id(project_id)}/duplicate', params=params, body=fields_object(fields) if fields is not None else {}))


@register_tool(
    namespace="vikunja",
    description="Mark a task as read. Clears the authenticated user's unread status for a task, dismissing the unread indicator raised by mentions and other task notifications. Idempotent: marking an already-read or inaccessible task succeeds as a no-op.",
    examples=['load_tool("vikunja.mark_task_read")(task_id=1)'],
    tool_class='write',
    aliases=[],
)
def mark_task_read(task_id: int, params: dict[str, Any] | None = None) -> Any:
    "PUT /api/v2/tasks/{task}/read. Clears the authenticated user's unread status for a task, dismissing the unread indicator raised by mentions and other task notifications. Idempotent: marking an already-read or inaccessible task succeeds as a no-op."
    client = get_client()
    return safe_response(safe_request(client, 'PUT', f'tasks/{positive_id(task_id)}/read', params=params))


@register_tool(
    namespace="vikunja",
    description="Healthcheck. Reports whether the service and its dependencies (database, Redis if enabled) are reachable. Returns 200 with status \"OK\" when healthy, 500 otherwise. When OpenID Connect providers are configured, each provider's availability is reported too; an unavailable provider (typically because it was unreachable while Vikunja started) degrades the status but never fails the check, since initialization is retried automatically (with exponential backoff, after at most 15 minutes) and a restart would not help. Public \u2014 no authentication required.",
    examples=['load_tool("vikunja.get_server_health")()'],
    tool_class='read',
    aliases=[],
)
def get_server_health(params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/health. Reports whether the service and its dependencies (database, Redis if enabled) are reachable. Returns 200 with status "OK" when healthy, 500 otherwise. When OpenID Connect providers are configured, each provider\'s availability is reported too; an unavailable provider (typically because it was unreachable while Vikunja started) degrades the status but never fails the check, since initialization is retried automatically (with exponential backoff, after at most 15 minutes) and a restart would not help. Public — no authentication required.'
    client = get_client()
    return safe_response(safe_request(client, 'GET', 'health', params=params, authenticated=False))

