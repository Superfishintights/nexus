"""Partial updates and task-planner operations built on Vikunja API v2."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import VikunjaError, fields_body, get_client, positive_id, validate_marker


@register_tool(namespace="vikunja", description="Check API v2 health and configured token access to projects.", examples=['load_tool("vikunja.get_health")()'], tool_class="read", aliases=[])
def get_health(check_auth: bool = True) -> dict[str, Any]:
    client = get_client()
    info = client.request("GET", "info", authenticated=False)
    result = {"healthy": True, "api_version": "v2", "info": info, "authenticated": None}
    if check_auth:
        client.page("projects", per_page=1)
        result["authenticated"] = True
    return result


@register_tool(namespace="vikunja", description="Partially update a task without replacing unmentioned fields.", examples=['load_tool("vikunja.update_task")(1, {"due_date": "2026-10-10T09:00:00Z"})'], tool_class="write", aliases=[])
def update_task(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    """Use ISO 8601 dates. Relationships, assignees and labels have dedicated endpoints."""
    return get_client().request("PATCH", f"tasks/{positive_id(task_id)}", body=fields, params=params)


@register_tool(namespace="vikunja", description="Partially update a project without replacing unmentioned fields.", examples=['load_tool("vikunja.update_project")(1, {"is_archived": True})'], tool_class="write", aliases=[])
def update_project(project_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    return get_client().request("PATCH", f"projects/{positive_id(project_id)}", body=fields, params=params)


@register_tool(namespace="vikunja", description="Partially update a label without replacing unmentioned fields.", examples=['load_tool("vikunja.update_label")(1, {"title": "Planning"})'], tool_class="write", aliases=[])
def update_label(label_id: int, fields: dict[str, Any]) -> Any:
    return get_client().request("PATCH", f"labels/{positive_id(label_id)}", body=fields)


@register_tool(namespace="vikunja", description="Partially update a project view without replacing unmentioned fields.", examples=['load_tool("vikunja.update_view")(1, 1, {"title": "Board"})'], tool_class="write", aliases=[])
def update_view(project_id: int, view_id: int, fields: dict[str, Any]) -> Any:
    return get_client().request("PATCH", f"projects/{positive_id(project_id)}/views/{positive_id(view_id)}", body=fields)


@register_tool(namespace="vikunja", description="Partially update a task comment written by the authenticated user.", examples=['load_tool("vikunja.update_task_comment")(1, 1, {"comment": "Updated plan"})'], tool_class="write", aliases=[])
def update_task_comment(task_id: int, comment_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    return get_client().request("PATCH", f"tasks/{positive_id(task_id)}/comments/{positive_id(comment_id)}", body=fields, params=params)


@register_tool(namespace="vikunja", description="Partially update an owned bot user's name or active status.", examples=['load_tool("vikunja.update_bot")(1, {"status": 2})'], tool_class="write", aliases=[])
def update_bot(bot_id: int, fields: dict[str, Any]) -> Any:
    return get_client().request("PATCH", f"user/bots/{positive_id(bot_id)}", body=fields)


@register_tool(namespace="vikunja", description="Complete or reopen a task; recurring tasks may advance dates and reopen automatically.", examples=['load_tool("vikunja.complete_task")(1, True)'], tool_class="write", aliases=[])
def complete_task(task_id: int, done: bool = True) -> Any:
    if not isinstance(done, bool):
        raise ValueError("done must be boolean")
    return update_task(task_id, {"done": done})


@register_tool(namespace="vikunja", description="Replace task reminders with absolute times or offsets from due, start or end dates.", examples=['load_tool("vikunja.set_task_reminders")(1, [{"relative_to": "due_date", "relative_period": -900}])'], tool_class="write", aliases=[])
def set_task_reminders(task_id: int, reminders: list[dict[str, Any]]) -> Any:
    """An empty list removes all reminders. Delivery depends on server notifications."""
    if not isinstance(reminders, list) or not all(isinstance(r, dict) for r in reminders):
        raise ValueError("reminders must be an array of objects")
    for reminder in reminders:
        if reminder.get("relative_to") not in {None, "", "due_date", "start_date", "end_date"}:
            raise ValueError("relative_to must be due_date, start_date or end_date")
        if not reminder.get("reminder") and not reminder.get("relative_to"):
            raise ValueError("Each reminder needs an absolute reminder time or relative_to")
    return update_task(task_id, {"reminders": reminders})


@register_tool(namespace="vikunja", description="Set recurrence seconds and mode: 0 after prior date, 1 monthly, 2 from completion date.", examples=['load_tool("vikunja.set_task_recurrence")(1, 86400, 0)'], tool_class="write", aliases=[])
def set_task_recurrence(task_id: int, repeat_after: int, repeat_mode: int = 0) -> Any:
    """Set repeat_after=0 with mode 0 to disable recurrence. There is no RRULE endpoint."""
    if isinstance(repeat_after, bool) or not isinstance(repeat_after, int) or repeat_after < 0:
        raise ValueError("repeat_after must be nonnegative seconds")
    if isinstance(repeat_mode, bool) or repeat_mode not in {0, 1, 2}:
        raise ValueError("repeat_mode must be 0, 1 or 2")
    return update_task(task_id, {"repeat_after": repeat_after, "repeat_mode": repeat_mode})


@register_tool(namespace="vikunja", description="Create a task in its parent's project and attach the subtask relation.", examples=['load_tool("vikunja.create_subtask")(1, "Prepare notes")'], tool_class="write", aliases=[])
def create_subtask(parent_task_id: int, title: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Two API writes. On relation failure, return partial=True and created_task for recovery."""
    client = get_client()
    parent = client.request("GET", f"tasks/{positive_id(parent_task_id)}")
    task = client.request("POST", f"projects/{positive_id(parent['project_id'])}/tasks", body=fields_body(title, fields))
    try:
        relation = client.request("POST", f"tasks/{parent_task_id}/relations", body={"other_task_id": task["id"], "relation_kind": "subtask"})
    except VikunjaError as exc:
        return {"created_task": task, "relation": None, "partial": True, "error": str(exc)}
    return {"created_task": task, "relation": relation, "partial": False}


@register_tool(namespace="vikunja", description="Read every visible task page up to an explicit bound; report truncated if more remain.", examples=['load_tool("vikunja.list_all_tasks")(max_pages=10)'], tool_class="read", aliases=[])
def list_all_tasks(project_id: int | None = None, params: dict[str, Any] | None = None, max_pages: int = 100, per_page: int = 50) -> dict[str, Any]:
    endpoint = "tasks" if project_id is None else f"projects/{positive_id(project_id)}/tasks"
    return get_client().all_pages(endpoint, params=params, max_pages=max_pages, per_page=per_page)


@register_tool(namespace="vikunja", description="Find exact personal-agent UUID markers in task descriptions with bounded pagination.", examples=['load_tool("vikunja.find_tasks_by_marker")("[personal-agent:00000000-0000-0000-0000-000000000001]")'], tool_class="read", aliases=[])
def find_tasks_by_marker(marker: str, project_id: int | None = None, max_pages: int = 100, per_page: int = 50) -> dict[str, Any]:
    """Use after an uncertain create response. A truncated result cannot prove absence."""
    validate_marker(marker)
    result = list_all_tasks(project_id, params={"format": "markdown"}, max_pages=max_pages, per_page=per_page)
    result["items"] = [task for task in result["items"] if marker in str(task.get("description") or "")]
    result["marker"] = marker
    return result


@register_tool(namespace="vikunja", description="Cancel a task only when its freshly read description contains the exact personal-agent UUID marker.", examples=['load_tool("vikunja.cancel_task")(1, "[personal-agent:00000000-0000-0000-0000-000000000001]")'], tool_class="destructive", aliases=[])
def cancel_task(task_id: int, marker: str) -> dict[str, Any]:
    """Delete an agent-owned task. This does not delete or mutate other tasks."""
    validate_marker(marker)
    client = get_client()
    endpoint = f"tasks/{positive_id(task_id)}"
    task = client.request("GET", endpoint, params={"format": "markdown"})
    if marker not in str(task.get("description") or ""):
        raise ValueError("Task ownership marker does not match; no cancellation performed")
    client.request("DELETE", endpoint)
    return {"cancelled": True, "task_id": task_id, "marker": marker}
