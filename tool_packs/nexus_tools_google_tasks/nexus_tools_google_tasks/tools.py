"""Google Tasks API v1 Nexus tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import (
    coerce_json,
    get_client,
    optional_bool,
    optional_int,
    optional_str,
    quote_path_segment,
)


def _clean(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in mapping.items() if value is not None}


def _task_path(tasklist_id: str, task_id: Optional[str] = None) -> str:
    path = f"lists/{quote_path_segment(tasklist_id)}/tasks"
    if task_id is not None:
        path = f"{path}/{quote_path_segment(task_id)}"
    return path


@register_tool(
    namespace="google_tasks",
    description="List Google Tasks task lists for the signed-in account.",
    examples=['load_tool("google_tasks.list_tasklists")(max_results=20)'],
    aliases=[],
    tool_class="read",
)
def list_tasklists(
    *,
    max_results: Optional[int] = 100,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        "users/@me/lists",
        method="GET",
        params=_clean({
            "maxResults": optional_int(max_results),
            "pageToken": optional_str(page_token),
        }),
    )


@register_tool(
    namespace="google_tasks",
    description="Get one Google Tasks task list by ID.",
    examples=['load_tool("google_tasks.get_tasklist")("@default")'],
    aliases=[],
    tool_class="read",
)
def get_tasklist(tasklist_id: str) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        f"users/@me/lists/{quote_path_segment(tasklist_id)}",
        method="GET",
    )


@register_tool(
    namespace="google_tasks",
    description="Create a Google Tasks task list.",
    examples=['load_tool("google_tasks.create_tasklist")("Work")'],
    aliases=[],
    tool_class="write",
)
def create_tasklist(title: str) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        "users/@me/lists",
        method="POST",
        payload={"title": title},
    )


@register_tool(
    namespace="google_tasks",
    description="Replace a Google Tasks task list resource.",
    examples=['load_tool("google_tasks.update_tasklist")("list_123", title="Work")'],
    aliases=[],
    tool_class="write",
)
def update_tasklist(tasklist_id: str, title: str) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        f"users/@me/lists/{quote_path_segment(tasklist_id)}",
        method="PUT",
        payload={"id": tasklist_id, "title": title},
    )


@register_tool(
    namespace="google_tasks",
    description="Patch fields on a Google Tasks task list.",
    examples=['load_tool("google_tasks.patch_tasklist")("list_123", title="Personal")'],
    aliases=[],
    tool_class="write",
)
def patch_tasklist(
    tasklist_id: str,
    *,
    title: Optional[str] = None,
    body: Optional[Any] = None,
) -> Dict[str, Any]:
    payload = coerce_json(body) or {}
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    if title is not None:
        payload["title"] = title
    return get_client().request(
        "tasks",
        f"users/@me/lists/{quote_path_segment(tasklist_id)}",
        method="PATCH",
        payload=payload,
    )


@register_tool(
    namespace="google_tasks",
    description="Delete a Google Tasks task list.",
    examples=['load_tool("google_tasks.delete_tasklist")("list_123")'],
    aliases=[],
    tool_class="destructive",
)
def delete_tasklist(tasklist_id: str) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        f"users/@me/lists/{quote_path_segment(tasklist_id)}",
        method="DELETE",
    )


@register_tool(
    namespace="google_tasks",
    description="List tasks in a Google Tasks task list with pagination and date filters.",
    examples=['load_tool("google_tasks.list_tasks")("@default", show_completed=False)'],
    aliases=[],
    tool_class="read",
)
def list_tasks(
    tasklist_id: str = "@default",
    *,
    max_results: Optional[int] = 100,
    page_token: Optional[str] = None,
    show_completed: Optional[bool] = True,
    show_deleted: Optional[bool] = False,
    show_hidden: Optional[bool] = False,
    due_min: Optional[str] = None,
    due_max: Optional[str] = None,
    completed_min: Optional[str] = None,
    completed_max: Optional[str] = None,
    updated_min: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        _task_path(tasklist_id),
        method="GET",
        params=_clean({
            "maxResults": optional_int(max_results),
            "pageToken": optional_str(page_token),
            "showCompleted": optional_bool(show_completed),
            "showDeleted": optional_bool(show_deleted),
            "showHidden": optional_bool(show_hidden),
            "dueMin": optional_str(due_min),
            "dueMax": optional_str(due_max),
            "completedMin": optional_str(completed_min),
            "completedMax": optional_str(completed_max),
            "updatedMin": optional_str(updated_min),
        }),
    )


@register_tool(
    namespace="google_tasks",
    description="Get one task from a Google Tasks task list.",
    examples=['load_tool("google_tasks.get_task")("@default", "task_123")'],
    aliases=[],
    tool_class="read",
)
def get_task(tasklist_id: str, task_id: str) -> Dict[str, Any]:
    return get_client().request("tasks", _task_path(tasklist_id, task_id), method="GET")


@register_tool(
    namespace="google_tasks",
    description="Create a task in a Google Tasks task list.",
    examples=['load_tool("google_tasks.create_task")("@default", title="Buy milk")'],
    aliases=[],
    tool_class="write",
)
def create_task(
    tasklist_id: str = "@default",
    *,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
    parent: Optional[str] = None,
    previous: Optional[str] = None,
    body: Optional[Any] = None,
) -> Dict[str, Any]:
    payload = coerce_json(body) or {}
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    payload.update(_clean({
        "title": optional_str(title),
        "notes": optional_str(notes),
        "due": optional_str(due),
        "status": optional_str(status),
    }))
    return get_client().request(
        "tasks",
        _task_path(tasklist_id),
        method="POST",
        params=_clean({
            "parent": optional_str(parent),
            "previous": optional_str(previous),
        }),
        payload=payload,
    )


@register_tool(
    namespace="google_tasks",
    description="Replace a Google Tasks task resource.",
    examples=['load_tool("google_tasks.update_task")("@default", "task_123", title="Done")'],
    aliases=[],
    tool_class="write",
)
def update_task(
    tasklist_id: str,
    task_id: str,
    *,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
    deleted: Optional[bool] = None,
    hidden: Optional[bool] = None,
    body: Optional[Any] = None,
) -> Dict[str, Any]:
    payload = coerce_json(body) or {}
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    payload.update(_clean({
        "id": task_id,
        "title": optional_str(title),
        "notes": optional_str(notes),
        "due": optional_str(due),
        "status": optional_str(status),
        "deleted": optional_bool(deleted),
        "hidden": optional_bool(hidden),
    }))
    return get_client().request(
        "tasks",
        _task_path(tasklist_id, task_id),
        method="PUT",
        payload=payload,
    )


@register_tool(
    namespace="google_tasks",
    description="Patch fields on a Google Tasks task.",
    examples=['load_tool("google_tasks.patch_task")("@default", "task_123", status="completed")'],
    aliases=[],
    tool_class="write",
)
def patch_task(
    tasklist_id: str,
    task_id: str,
    *,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
    deleted: Optional[bool] = None,
    hidden: Optional[bool] = None,
    body: Optional[Any] = None,
) -> Dict[str, Any]:
    payload = coerce_json(body) or {}
    if not isinstance(payload, dict):
        raise ValueError("body must be a JSON object")
    payload.update(_clean({
        "title": optional_str(title),
        "notes": optional_str(notes),
        "due": optional_str(due),
        "status": optional_str(status),
        "deleted": optional_bool(deleted),
        "hidden": optional_bool(hidden),
    }))
    return get_client().request(
        "tasks",
        _task_path(tasklist_id, task_id),
        method="PATCH",
        payload=payload,
    )


@register_tool(
    namespace="google_tasks",
    description="Delete a task from a Google Tasks task list.",
    examples=['load_tool("google_tasks.delete_task")("@default", "task_123")'],
    aliases=[],
    tool_class="destructive",
)
def delete_task(tasklist_id: str, task_id: str) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        _task_path(tasklist_id, task_id),
        method="DELETE",
    )


@register_tool(
    namespace="google_tasks",
    description="Move a Google Tasks task within a list or to another task list.",
    examples=['load_tool("google_tasks.move_task")("@default", "task_123", previous="task_122")'],
    aliases=[],
    tool_class="write",
)
def move_task(
    tasklist_id: str,
    task_id: str,
    *,
    parent: Optional[str] = None,
    previous: Optional[str] = None,
    destination_tasklist: Optional[str] = None,
) -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        f"{_task_path(tasklist_id, task_id)}/move",
        method="POST",
        params=_clean({
            "parent": optional_str(parent),
            "previous": optional_str(previous),
            "destinationTasklist": optional_str(destination_tasklist),
        }),
    )


@register_tool(
    namespace="google_tasks",
    description="Clear all completed tasks from a Google Tasks task list.",
    examples=['load_tool("google_tasks.clear_completed_tasks")("@default")'],
    aliases=[],
    tool_class="destructive",
)
def clear_completed_tasks(tasklist_id: str = "@default") -> Dict[str, Any]:
    return get_client().request(
        "tasks",
        f"lists/{quote_path_segment(tasklist_id)}/clear",
        method="POST",
    )
