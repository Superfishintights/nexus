"""Vikunja API v2 tools. See the pack README and versioned official spec."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description='List tasks in a project.', examples=['load_tool("vikunja.list_project_tasks")(1)'], tool_class='read', aliases=[])
def list_project_tasks(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the tasks in a project, paginated and flat. Requires read access to the project. Filtering, sorting and search apply to every variant. See https://vikunja.io/docs/filters for the filter language.'
    return get_client().page(f'projects/{positive_id(project_id)}/tasks', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a task.', examples=['load_tool("vikunja.create_task")(1, \'Nexus integration test\')'], tool_class='write', aliases=[])
def create_task(project_id: int, title: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    "Creates a task in the project from the URL. The authenticated user needs write access to that project and becomes the task's creator."
    return get_client().request('POST', f'projects/{positive_id(project_id)}/tasks', params=params, body=fields_body(title, fields))


@register_tool(namespace="vikunja", description='Create multiple tasks.', examples=['load_tool("vikunja.create_tasks_bulk")(1, {})'], tool_class='write', aliases=[])
def create_tasks_bulk(project_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Creates up to 100 tasks in the project from the URL in one atomic request: if any task is invalid, none are created and the error names the failing index. Tasks are created in payload order and land on top of every view in that order. The authenticated user needs write access to the project and becomes the creator of every task. Bucket limits are only enforced for tasks with an explicit bucket_id; tasks left to land in a view's default bucket are not counted against its limit."
    return get_client().request('POST', f'projects/{positive_id(project_id)}/tasks/bulk', params=params, body=fields)


@register_tool(namespace="vikunja", description='Get a task by its project index.', examples=['load_tool("vikunja.get_task_by_index")(\'bot-assistant\', 1)'], tool_class='read', aliases=[])
def get_task_by_index(project_id: str, index: int, params: dict[str, Any] | None = None) -> Any:
    'Returns a single task addressed by its per-project index. Historical addresses redirect. The {project} segment accepts either a numeric project id or a textual project identifier (e.g. "PROJ"); a value made solely of digits is always treated as an id. Embed extra, more expensive data in each task. Repeatable. One of: subtasks, buckets, reactions, comments, comment_count, time_entries_count, is_unread. Expanding can return more tasks than the page limit (subtasks) and inflate the response.'
    return get_client().request('GET', f'projects/{path_text(project_id)}/tasks/by-index/{positive_id(index)}', params=params)


@register_tool(namespace="vikunja", description="List a kanban view's buckets with their tasks.", examples=['load_tool("vikunja.list_bucket_tasks")(1, 1)'], tool_class='read', aliases=[])
def list_bucket_tasks(project_id: int, view_id: int, params: dict[str, Any] | None = None) -> Any:
    "Returns the buckets of a project's kanban view, each populated with the tasks in it. Requires read access to the project. Not paginated: the number and size of buckets follow the view's bucket configuration, so page/per_page do not apply. Filtering, sorting and search apply to every variant. See https://vikunja.io/docs/filters for the filter language."
    return get_client().request('GET', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/buckets/tasks', params=params)


@register_tool(namespace="vikunja", description='Place a task in a kanban bucket.', examples=['load_tool("vikunja.move_task_to_bucket")(1, 1, 1, {})'], tool_class='write', aliases=[])
def move_task_to_bucket(project_id: int, view_id: int, bucket_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Moves a task into the given bucket of a project's kanban view. Requires write access to the project. Idempotent: re-sending the same bucket is a no-op. Side effects: moving a task into the view's done bucket marks it done (and out of it un-marks it); a repeating task moved into the done bucket is reopened and routed back to the default bucket instead. Moving a task into a bucket that is already at its task limit is rejected with 412. A bucket that does not resolve under the project and view in the path is rejected with 404."
    return get_client().request('PUT', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/buckets/{positive_id(bucket_id)}/tasks', params=params, body=fields)


@register_tool(namespace="vikunja", description='List tasks in a project view.', examples=['load_tool("vikunja.list_view_tasks")(1, 1)'], tool_class='read', aliases=[])
def list_view_tasks(project_id: int, view_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    "Returns the tasks in a project view, paginated and flat. The view's own filter, sort and search are applied on top of the query. Always returns flat tasks, even for a kanban view — use the buckets endpoint to get tasks grouped by bucket. Filtering, sorting and search apply to every variant. See https://vikunja.io/docs/filters for the filter language."
    return get_client().page(f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/tasks', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='List tasks across all projects.', examples=['load_tool("vikunja.list_tasks")()'], tool_class='read', aliases=[])
def list_tasks(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the tasks the authenticated user can see across every project they have access to, paginated and flat. Filtering, sorting and search apply to every variant. See https://vikunja.io/docs/filters for the filter language.'
    return get_client().page('tasks', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Bulk update tasks.', examples=['load_tool("vikunja.update_tasks_bulk")({})'], tool_class='write', aliases=[])
def update_tasks_bulk(fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Applies the fields named in `fields` from `values` to every task in `task_ids`. The user needs write access to every project the involved tasks belong to; if write is missing on even one, the whole request is rejected and nothing is changed. Returns the updated tasks.'
    return get_client().request('PUT', 'tasks/bulk', params=params, body=fields)


@register_tool(namespace="vikunja", description='Delete a task.', examples=['load_tool("vikunja.delete_task")(1)'], tool_class='destructive', aliases=[])
def delete_task(task_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a task. Requires write access to its project.'
    return get_client().request('DELETE', f'tasks/{positive_id(task_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a task.', examples=['load_tool("vikunja.get_task")(1)'], tool_class='read', aliases=[])
def get_task(task_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns a single task by its numeric id. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified. Embed extra, more expensive data in each task. Repeatable. One of: subtasks, buckets, reactions, comments, comment_count, time_entries_count, is_unread. Expanding can return more tasks than the page limit (subtasks) and inflate the response.'
    return get_client().request('GET', f'tasks/{positive_id(task_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a task. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_task")(1, {})'], tool_class='write', aliases=[])
def replace_task(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces all of a task's fields; requires write access. Setting project_id to a different project moves the task and also requires write access to the target project. Use PATCH for a partial update."
    return get_client().request('PUT', f'tasks/{positive_id(task_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='List the assignees of a task.', examples=['load_tool("vikunja.list_task_assignees")(1)'], tool_class='read', aliases=[])
def list_task_assignees(task_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the users assigned to the given task, paginated. Requires read access to the task. Pass q to filter assignees by username.'
    return get_client().page(f'tasks/{positive_id(task_id)}/assignees', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Assign a user to a task.', examples=['load_tool("vikunja.add_task_assignee")(1, {})'], tool_class='write', aliases=[])
def add_task_assignee(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Assigns a user to the given task. The parent task is taken from the URL; the assignee is named by user_id in the body. The assignee must have access to the task's project, and the caller needs write access to the task."
    return get_client().request('POST', f'tasks/{positive_id(task_id)}/assignees', params=params, body=fields)


@register_tool(namespace="vikunja", description='Replace all assignees of a task. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_task_assignees")(1, {})'], tool_class='write', aliases=[])
def replace_task_assignees(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces the task's full assignee set with the users in the body: users not in the list are unassigned, new ones are added. Pass an empty array to unassign everyone. Each assignee must have access to the task's project, and the caller needs write access to the task."
    return get_client().request('PUT', f'tasks/{positive_id(task_id)}/assignees/bulk', params=params, body=fields)


@register_tool(namespace="vikunja", description='Remove an assignee from a task.', examples=['load_tool("vikunja.remove_task_assignee")(1, 1)'], tool_class='destructive', aliases=[])
def remove_task_assignee(task_id: int, user_id: int, params: dict[str, Any] | None = None) -> Any:
    'Un-assigns a user from the given task, identified by their user id in the path. Requires write access to the task.'
    return get_client().request('DELETE', f'tasks/{positive_id(task_id)}/assignees/{positive_id(user_id)}', params=params)


@register_tool(namespace="vikunja", description='List the comments of a task.', examples=['load_tool("vikunja.list_task_comments")(1)'], tool_class='read', aliases=[])
def list_task_comments(task_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the comments of the given task, paginated. Requires read access to the task. Pass order_by=desc to sort newest-first (default is oldest-first).'
    return get_client().page(f'tasks/{positive_id(task_id)}/comments', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a comment on a task.', examples=['load_tool("vikunja.create_task_comment")(1, {})'], tool_class='write', aliases=[])
def create_task_comment(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Adds a comment to the given task. The parent task is taken from the URL, not the body, and the author is the authenticated user. Requires write access to the task.'
    return get_client().request('POST', f'tasks/{positive_id(task_id)}/comments', params=params, body=fields)


@register_tool(namespace="vikunja", description='Delete a comment of a task.', examples=['load_tool("vikunja.delete_task_comment")(1, 1)'], tool_class='destructive', aliases=[])
def delete_task_comment(task_id: int, comment_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a comment of a task. The comment must belong to the task in the path, and only its author may delete it.'
    return get_client().request('DELETE', f'tasks/{positive_id(task_id)}/comments/{positive_id(comment_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a single comment of a task.', examples=['load_tool("vikunja.get_task_comment")(1, 1)'], tool_class='read', aliases=[])
def get_task_comment(task_id: int, comment_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns one comment of a task. The comment must belong to the task in the path. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    return get_client().request('GET', f'tasks/{positive_id(task_id)}/comments/{positive_id(comment_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a comment of a task. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_task_comment")(1, 1, {})'], tool_class='write', aliases=[])
def replace_task_comment(task_id: int, comment_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces a comment's text. The comment must belong to the task in the path, and only its author may update it. Use PATCH for a partial update."
    return get_client().request('PUT', f'tasks/{positive_id(task_id)}/comments/{positive_id(comment_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='Duplicate a task.', examples=['load_tool("vikunja.duplicate_task")(1)'], tool_class='write', aliases=[])
def duplicate_task(task_id: int, params: dict[str, Any] | None = None) -> Any:
    'Copies a task — including its labels, assignees, attachments and reminders — into the same project, and records a "copied from" relation back to the original. The authenticated user needs read access to the source task and write access to its project. Returns the newly created duplicate.'
    return get_client().request('POST', f'tasks/{positive_id(task_id)}/duplicate', params=params)


@register_tool(namespace="vikunja", description='List the labels on a task.', examples=['load_tool("vikunja.list_task_labels")(1)'], tool_class='read', aliases=[])
def list_task_labels(task_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the labels attached to the given task, paginated. Requires read access to the task.'
    return get_client().page(f'tasks/{positive_id(task_id)}/labels', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Add a label to a task.', examples=['load_tool("vikunja.add_task_label")(1, {})'], tool_class='write', aliases=[])
def add_task_label(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Attaches an existing label to the given task. Requires write access to the task and access to the label. Fails if the label is already on the task.'
    return get_client().request('POST', f'tasks/{positive_id(task_id)}/labels', params=params, body=fields)


@register_tool(namespace="vikunja", description='Replace all labels on a task. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_task_labels")(1, {})'], tool_class='write', aliases=[])
def replace_task_labels(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Sets the task's labels to exactly the provided list: labels not in the list are removed, missing ones are added, unchanged ones are left alone. Requires write access to the task, and you must be able to see every label you attach. Returns the resulting label set."
    return get_client().request('PUT', f'tasks/{positive_id(task_id)}/labels/bulk', params=params, body=fields)


@register_tool(namespace="vikunja", description='Remove a label from a task.', examples=['load_tool("vikunja.remove_task_label")(1, 1)'], tool_class='destructive', aliases=[])
def remove_task_label(task_id: int, label_id: int, params: dict[str, Any] | None = None) -> Any:
    'Detaches a label from the given task. Requires write access to the task.'
    return get_client().request('DELETE', f'tasks/{positive_id(task_id)}/labels/{positive_id(label_id)}', params=params)


@register_tool(namespace="vikunja", description="Set a task's position in a view.", examples=['load_tool("vikunja.set_task_position")(1, {})'], tool_class='write', aliases=[])
def set_task_position(task_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Sets where a task sorts within one of its project's views. The position is per view, so this only affects the view named by project_view_id. Requires write access to the task. Positions below the minimum spacing make the server recalculate every position in the view, so the returned value may differ from the one sent."
    return get_client().request('PUT', f'tasks/{positive_id(task_id)}/position', params=params, body=fields)


@register_tool(namespace="vikunja", description='Create a task relation.', examples=['load_tool("vikunja.add_task_relation")(1, 2, "related")'], tool_class='write', aliases=[])
def add_task_relation(task_id: int, other_task_id: int, relation_kind: str, params: dict[str, Any] | None = None) -> Any:
    'Relates two tasks. The authenticated user needs write access to the base task (in the path) and at least read access to the other task; the two tasks need not share a project. The inverse relation is created automatically (e.g. a subtask relation also stores the parenttask relation on the other task). Subtask/parenttask chains that would form a cycle are rejected.'
    if relation_kind not in {'subtask', 'parenttask', 'related', 'duplicateof', 'duplicates', 'blocking', 'blocked', 'precedes', 'follows', 'copiedfrom', 'copiedto'}:
        raise ValueError('Unsupported relation_kind')
    return get_client().request('POST', f'tasks/{positive_id(task_id)}/relations', params=params, body={'other_task_id': positive_id(other_task_id), 'relation_kind': relation_kind})


@register_tool(namespace="vikunja", description='Delete a task relation.', examples=['load_tool("vikunja.remove_task_relation")(1, \'related\', 1)'], tool_class='destructive', aliases=[])
def remove_task_relation(task_id: int, relation_kind: str, other_task_id: int, params: dict[str, Any] | None = None) -> Any:
    'Removes the relation identified by the base task, relation kind and other task. The automatically created inverse relation is removed as well. The authenticated user needs write access to the base task.'
    return get_client().request('DELETE', f'tasks/{positive_id(task_id)}/relations/{path_text(relation_kind)}/{positive_id(other_task_id)}', params=params)
