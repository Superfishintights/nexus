"""Approved Vikunja API v2 ordinary operations, derived from deployed v2.7.0."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text
from ._ordinary import safe_response, safe_request, fields_object, time_entry_fields, subscription_entity, session_uuid


@register_tool(
    namespace="vikunja",
    description="List time entries. Returns the time entries the authenticated user can see, paginated. Filterable by date range, project, task and user. Query parameters: [{\"name\":\"page\",\"description\":\"1-based page number.\",\"schema\":{\"default\":1,\"description\":\"1-based page number.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"per_page\",\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"schema\":{\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"q\",\"description\":\"Search query; filters the list to items matching this string.\",\"schema\":{\"description\":\"Search query; filters the list to items matching this string.\",\"type\":\"string\"}},{\"name\":\"filter\",\"description\":\"Filter entries with the task filter syntax over user_id, task_id, project_id, start_time and end_time \\u2014 e.g. \\\"project_id = 5 && start_time > now-7d\\\". Use end_time = null to match running timers.\",\"schema\":{\"description\":\"Filter entries with the task filter syntax over user_id, task_id, project_id, start_time and end_time \\u2014 e.g. \\\"project_id = 5 && start_time > now-7d\\\". Use end_time = null to match running timers.\",\"type\":\"string\"}},{\"name\":\"filter_timezone\",\"description\":\"IANA timezone name used to resolve relative dates (now, now-7d) in the filter, e.g. Europe/Berlin.\",\"schema\":{\"description\":\"IANA timezone name used to resolve relative dates (now, now-7d) in the filter, e.g. Europe/Berlin.\",\"type\":\"string\"}}]",
    examples=['load_tool("vikunja.list_time_entries")()'],
    tool_class='read',
    aliases=[],
)
def list_time_entries(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/time-entries. Returns the time entries the authenticated user can see, paginated. Filterable by date range, project, task and user.'
    client = get_client()
    return safe_response(client.page('time-entries', page=page, per_page=per_page, params={**(params or {}), **({'q': query} if query is not None else {})}))


@register_tool(
    namespace="vikunja",
    description="Create a time entry. Logs a manual time entry for the authenticated user. Exactly one of task_id / project_id must be set. fields requires exactly one positive task_id or project_id. Set start_time and end_time; end_time=null starts a running timer. Request body schema: {\"content\":{\"application/json\":{\"schema\":{\"$ref\":\"#/components/schemas/TimeEntry\"}}},\"required\":true}",
    examples=['load_tool("vikunja.create_time_entry")(fields={"task_id":1,"start_time":"2026-10-04T09:00:00Z","end_time":None})'],
    tool_class='write',
    aliases=[],
)
def create_time_entry(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'POST /api/v2/time-entries. Logs a manual time entry for the authenticated user. Exactly one of task_id / project_id must be set.'
    client = get_client()
    return safe_response(safe_request(client, 'POST', 'time-entries', params=params, body=time_entry_fields(fields)))


@register_tool(
    namespace="vikunja",
    description="Get a time entry. Returns a single time entry. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.",
    examples=['load_tool("vikunja.get_time_entry")(time_entry_id=1)'],
    tool_class='read',
    aliases=[],
)
def get_time_entry(time_entry_id: int, params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/time-entries/{id}. Returns a single time entry. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    client = get_client()
    return safe_response(safe_request(client, 'GET', f'time-entries/{positive_id(time_entry_id)}', params=params))


@register_tool(
    namespace="vikunja",
    description="Update a time entry (partial). Partial update operation supporting both JSON Merge Patch & JSON Patch updates. Uses JSON Merge Patch: send only changed fields, including explicit null when needed. Request body schema: {\"content\":{\"application/json-patch+json\":{\"schema\":{\"items\":{\"$ref\":\"#/components/schemas/JsonPatchOp\"},\"type\":[\"array\",\"null\"]}},\"application/merge-patch+json\":{\"schema\":{\"additionalProperties\":false,\"properties\":{\"$schema\":{\"description\":\"A URL to the JSON Schema for this object.\",\"examples\":[\"/api/v2/schemas/TimeEntryReadBody.json\"],\"format\":\"uri\",\"readOnly\":true,\"type\":\"string\"},\"comment\":{\"description\":\"An optional comment describing the logged time.\",\"type\":\"string\"},\"created\":{\"description\":\"A timestamp when this time entry was created. You cannot change this value.\",\"format\":\"date-time\",\"readOnly\":true,\"type\":\"string\"},\"end_time\":{\"description\":\"When the tracked time ended. Null means a live timer is still running.\",\"format\":\"date-time\",\"type\":\"string\"},\"id\":{\"description\":\"The unique, numeric id of this time entry.\",\"format\":\"int64\",\"readOnly\":true,\"type\":\"integer\"},\"max_permission\":{\"description\":\"The maximum permission the requesting user has on this time entry (0=read, 1=read/write, 2=admin).\",\"format\":\"int64\",\"readOnly\":true,\"type\":\"integer\"},\"project_id\":{\"description\":\"The project this entry is attached to directly. Exactly one of task_id / project_id must be set.\",\"format\":\"int64\",\"type\":\"integer\"},\"start_time\":{\"description\":\"When the tracked time started.\",\"format\":\"date-time\",\"type\":\"string\"},\"task_id\":{\"description\":\"The task this entry is attached to. Exactly one of task_id / project_id must be set.\",\"format\":\"int64\",\"type\":\"integer\"},\"updated\":{\"description\":\"A timestamp when this time entry was last updated. You cannot change this value.\",\"format\":\"date-time\",\"readOnly\":true,\"type\":\"string\"},\"user_id\":{\"description\":\"The id of the user who logged this time entry. Set by the server.\",\"format\":\"int64\",\"readOnly\":true,\"type\":\"integer\"}},\"type\":\"object\"}},\"application/merge-patch+shorthand\":{\"schema\":{\"additionalProperties\":false,\"properties\":{\"$schema\":{\"description\":\"A URL to the JSON Schema for this object.\",\"examples\":[\"/api/v2/schemas/TimeEntryReadBody.json\"],\"format\":\"uri\",\"readOnly\":true,\"type\":\"string\"},\"comment\":{\"description\":\"An optional comment describing the logged time.\",\"type\":\"string\"},\"created\":{\"description\":\"A timestamp when this time entry was created. You cannot change this value.\",\"format\":\"date-time\",\"readOnly\":true,\"type\":\"string\"},\"end_time\":{\"description\":\"When the tracked time ended. Null means a live timer is still running.\",\"format\":\"date-time\",\"type\":\"string\"},\"id\":{\"description\":\"The unique, numeric id of this time entry.\",\"format\":\"int64\",\"readOnly\":true,\"type\":\"integer\"},\"max_permission\":{\"description\":\"The maximum permission the requesting user has on this time entry (0=read, 1=read/write, 2=admin).\",\"format\":\"int64\",\"readOnly\":true,\"type\":\"integer\"},\"project_id\":{\"description\":\"The project this entry is attached to directly. Exactly one of task_id / project_id must be set.\",\"format\":\"int64\",\"type\":\"integer\"},\"start_time\":{\"description\":\"When the tracked time started.\",\"format\":\"date-time\",\"type\":\"string\"},\"task_id\":{\"description\":\"The task this entry is attached to. Exactly one of task_id / project_id must be set.\",\"format\":\"int64\",\"type\":\"integer\"},\"updated\":{\"description\":\"A timestamp when this time entry was last updated. You cannot change this value.\",\"format\":\"date-time\",\"readOnly\":true,\"type\":\"string\"},\"user_id\":{\"description\":\"The id of the user who logged this time entry. Set by the server.\",\"format\":\"int64\",\"readOnly\":true,\"type\":\"integer\"}},\"type\":\"object\"}}},\"required\":true}",
    examples=['load_tool("vikunja.update_time_entry")(time_entry_id=1, fields={"comment":"Planning"})'],
    tool_class='write',
    aliases=[],
)
def update_time_entry(time_entry_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'PATCH /api/v2/time-entries/{id}. Partial update operation supporting both JSON Merge Patch & JSON Patch updates.'
    client = get_client()
    return safe_response(safe_request(client, 'PATCH', f'time-entries/{positive_id(time_entry_id)}', params=params, body=fields_object(fields), headers={'Content-Type':'application/merge-patch+json'}))


@register_tool(
    namespace="vikunja",
    description="Update a time entry. Updates a time entry. Only the author may update it. The entry can be moved between a task and a project \u2014 exactly one of task_id / project_id must be set, and you need read access to the new one. PUT replaces all editable fields; use PATCH for a partial update. Full replacement can reset omitted fields. Prefer the partial update tool for sparse changes. Request body schema: {\"content\":{\"application/json\":{\"schema\":{\"$ref\":\"#/components/schemas/TimeEntryReadBody\"}}},\"required\":true}",
    examples=['load_tool("vikunja.replace_time_entry")(time_entry_id=1, fields={"task_id":1,"start_time":"2026-10-04T09:00:00Z","end_time":"2026-10-04T09:30:00Z"})'],
    tool_class='write',
    aliases=[],
)
def replace_time_entry(time_entry_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'PUT /api/v2/time-entries/{id}. Updates a time entry. Only the author may update it. The entry can be moved between a task and a project — exactly one of task_id / project_id must be set, and you need read access to the new one. PUT replaces all editable fields; use PATCH for a partial update.'
    client = get_client()
    return safe_response(safe_request(client, 'PUT', f'time-entries/{positive_id(time_entry_id)}', params=params, body=time_entry_fields(fields)))


@register_tool(
    namespace="vikunja",
    description="Delete a time entry. Deletes a time entry. Only the author may delete it. If it is the running timer, deleting it removes that timer.",
    examples=['load_tool("vikunja.delete_time_entry")(time_entry_id=1)'],
    tool_class='destructive',
    aliases=[],
)
def delete_time_entry(time_entry_id: int, params: dict[str, Any] | None = None) -> Any:
    'DELETE /api/v2/time-entries/{id}. Deletes a time entry. Only the author may delete it. If it is the running timer, deleting it removes that timer.'
    client = get_client()
    return safe_response(safe_request(client, 'DELETE', f'time-entries/{positive_id(time_entry_id)}', params=params))


@register_tool(
    namespace="vikunja",
    description="Stop the running timer. Stops the authenticated user's running timer, setting its end time to the server's current time, and returns the stopped entry. Returns 404 when no timer is running. Starting a timer and editing entries go through the regular create/update endpoints.",
    examples=['load_tool("vikunja.stop_timer")()'],
    tool_class='write',
    aliases=[],
)
def stop_timer(params: dict[str, Any] | None = None) -> Any:
    "POST /api/v2/time-entries/timer/stop. Stops the authenticated user's running timer, setting its end time to the server's current time, and returns the stopped entry. Returns 404 when no timer is running. Starting a timer and editing entries go through the regular create/update endpoints."
    client = get_client()
    return safe_response(safe_request(client, 'POST', 'time-entries/timer/stop', params=params))


@register_tool(
    namespace="vikunja",
    description="List a task's time entries. Returns the time entries logged against the given task, across all users, paginated. Scoped to what you can read: an inaccessible or unknown task yields an empty list, not an error. Query parameters: [{\"name\":\"page\",\"description\":\"1-based page number.\",\"schema\":{\"default\":1,\"description\":\"1-based page number.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"per_page\",\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"schema\":{\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"q\",\"description\":\"Search query; filters the list to items matching this string.\",\"schema\":{\"description\":\"Search query; filters the list to items matching this string.\",\"type\":\"string\"}}]",
    examples=['load_tool("vikunja.list_task_time_entries")(task_id=1)'],
    tool_class='read',
    aliases=[],
)
def list_task_time_entries(task_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/tasks/{task_id}/time-entries. Returns the time entries logged against the given task, across all users, paginated. Scoped to what you can read: an inaccessible or unknown task yields an empty list, not an error.'
    client = get_client()
    return safe_response(client.page(f'tasks/{positive_id(task_id)}/time-entries', page=page, per_page=per_page, params={**(params or {}), **({'q': query} if query is not None else {})}))


@register_tool(
    namespace="vikunja",
    description="List a project's time entries. Returns the time entries for the given project \u2014 both standalone project entries and entries on tasks currently in the project \u2014 paginated. Scoped to what you can read: an inaccessible or unknown project yields an empty list, not an error. Query parameters: [{\"name\":\"page\",\"description\":\"1-based page number.\",\"schema\":{\"default\":1,\"description\":\"1-based page number.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"per_page\",\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"schema\":{\"description\":\"Items per page. Defaults to the instance's configured maximum (service.maxitemsperpage, reported as max_items_per_page by /info) and is silently capped at it; asking for more is not an error.\",\"format\":\"int64\",\"minimum\":1,\"type\":\"integer\"}},{\"name\":\"q\",\"description\":\"Search query; filters the list to items matching this string.\",\"schema\":{\"description\":\"Search query; filters the list to items matching this string.\",\"type\":\"string\"}}]",
    examples=['load_tool("vikunja.list_project_time_entries")(project_id=1)'],
    tool_class='read',
    aliases=[],
)
def list_project_time_entries(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'GET /api/v2/projects/{project_id}/time-entries. Returns the time entries for the given project — both standalone project entries and entries on tasks currently in the project — paginated. Scoped to what you can read: an inaccessible or unknown project yields an empty list, not an error.'
    client = get_client()
    return safe_response(client.page(f'projects/{positive_id(project_id)}/time-entries', page=page, per_page=per_page, params={**(params or {}), **({'q': query} if query is not None else {})}))

