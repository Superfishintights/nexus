"""Vikunja API v2 tools. See the pack README and versioned official spec."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description='List projects.', examples=['load_tool("vikunja.list_projects")()'], tool_class='read', aliases=[])
def list_projects(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    "Returns the projects the authenticated user has access to (owned plus shared, with child projects of accessible parents), paginated. Archived projects are excluded unless is_archived=true. Pass expand=permissions to include each project's max_permission for the caller."
    return get_client().page('projects', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a project.', examples=['load_tool("vikunja.create_project")(\'Nexus integration test\')'], tool_class='write', aliases=[])
def create_project(title: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'Creates a project; the authenticated user becomes its owner. When parent_project_id is set, the caller needs write access to that parent. Default views and a backlog bucket are created automatically.'
    return get_client().request('POST', 'projects', params=params, body=fields_body(title, fields))


@register_tool(namespace="vikunja", description='Delete a project.', examples=['load_tool("vikunja.delete_project")(1)'], tool_class='destructive', aliases=[])
def delete_project(project_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a project together with its tasks, views, buckets and child projects. Only project admins may delete it.'
    return get_client().request('DELETE', f'projects/{positive_id(project_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a project.', examples=['load_tool("vikunja.get_project")(1)'], tool_class='read', aliases=[])
def get_project(project_id: int, params: dict[str, Any] | None = None) -> Any:
    "Returns a single project the caller can read, including its views, the caller's favorite/subscription state and the caller's max_permission. Resolves the Favorites pseudo-project and saved-filter-backed projects. Served fresh on every call (no conditional/ETag) because the response carries user-scoped state that changes without bumping the project's updated timestamp."
    return get_client().request('GET', f'projects/{positive_id(project_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a project. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_project")(1, {})'], tool_class='write', aliases=[])
def replace_project(project_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces a project's fields. Requires write access (admin to reparent or delete). Use PATCH for a partial update."
    return get_client().request('PUT', f'projects/{positive_id(project_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='List the teams a project is shared with.', examples=['load_tool("vikunja.list_project_teams")(1)'], tool_class='read', aliases=[])
def list_project_teams(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the teams that have access to the project, each with the permission they were granted. Requires read access to the project.'
    return get_client().page(f'projects/{positive_id(project_id)}/teams', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Share a project with a team.', examples=['load_tool("vikunja.share_project_with_team")(1, {})'], tool_class='write', aliases=[])
def share_project_with_team(project_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Gives a team access to the project at the requested permission. Only project admins may share. Fails if the team already has access.'
    return get_client().request('POST', f'projects/{positive_id(project_id)}/teams', params=params, body=fields)


@register_tool(namespace="vikunja", description='Remove a team from a project.', examples=['load_tool("vikunja.remove_project_team")(1, 1)'], tool_class='destructive', aliases=[])
def remove_project_team(project_id: int, team_id: int, params: dict[str, Any] | None = None) -> Any:
    "Revokes a team's access to the project. Only project admins may remove a share."
    return get_client().request('DELETE', f'projects/{positive_id(project_id)}/teams/{positive_id(team_id)}', params=params)


@register_tool(namespace="vikunja", description="Update a team's permission on a project.", examples=['load_tool("vikunja.update_project_team_permission")(1, 1, {})'], tool_class='write', aliases=[])
def update_project_team_permission(project_id: int, team_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Changes the permission a team has on the project; only the permission is writable. Only project admins may update a share.'
    return get_client().request('PUT', f'projects/{positive_id(project_id)}/teams/{positive_id(team_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='List the users a project is shared with.', examples=['load_tool("vikunja.list_project_users")(1)'], tool_class='read', aliases=[])
def list_project_users(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the users that have direct access to the project, with their permission. Requires read access to the project; team shares are not included. Pass q to filter by username.'
    return get_client().page(f'projects/{positive_id(project_id)}/users', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Share a project with a user.', examples=['load_tool("vikunja.share_project_with_user")(1, {})'], tool_class='write', aliases=[])
def share_project_with_user(project_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Grants a user access to the project. The user is named by username in the body. Only project admins may share; the project owner cannot be added.'
    return get_client().request('POST', f'projects/{positive_id(project_id)}/users', params=params, body=fields)


@register_tool(namespace="vikunja", description='Search users with access to a project.', examples=['load_tool("vikunja.search_project_users")(1)'], tool_class='read', aliases=[])
def search_project_users(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the users who can access the project — through ownership, a direct share or a team — optionally filtered by a search string. Intended for share autocomplete. Requires read access to the project.'
    return get_client().page(f'projects/{positive_id(project_id)}/users/search', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description="Remove a user's access to a project.", examples=['load_tool("vikunja.remove_project_user")(1, \'bot-assistant\')'], tool_class='destructive', aliases=[])
def remove_project_user(project_id: int, username: str, params: dict[str, Any] | None = None) -> Any:
    "Revokes a user's direct access to the project, identified by username in the path. Only project admins may do this."
    return get_client().request('DELETE', f'projects/{positive_id(project_id)}/users/{path_text(username)}', params=params)


@register_tool(namespace="vikunja", description="Update a user's permission on a project.", examples=['load_tool("vikunja.update_project_user_permission")(1, \'bot-assistant\', {})'], tool_class='write', aliases=[])
def update_project_user_permission(project_id: int, username: str, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    'Changes the permission a user has on the project; only the permission field is updated. The user is identified by username in the path. Only project admins may update a share.'
    return get_client().request('PUT', f'projects/{positive_id(project_id)}/users/{path_text(username)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='List the views of a project.', examples=['load_tool("vikunja.list_views")(1)'], tool_class='read', aliases=[])
def list_views(project_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns all views of the given project. Requires read access to the project; the list is not paginated by the server but is returned in the standard list envelope.'
    return get_client().page(f'projects/{positive_id(project_id)}/views', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a view in a project.', examples=['load_tool("vikunja.create_view")(1, \'Nexus integration test\')'], tool_class='write', aliases=[])
def create_view(project_id: int, title: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'Creates a view in the given project. The parent project is taken from the URL, not the body. Only project admins may create a view.'
    return get_client().request('POST', f'projects/{positive_id(project_id)}/views', params=params, body=fields_body(title, fields))


@register_tool(namespace="vikunja", description='Delete a view of a project.', examples=['load_tool("vikunja.delete_view")(1, 1)'], tool_class='destructive', aliases=[])
def delete_view(project_id: int, view_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a project view along with its buckets and task positions. Only project admins may delete it.'
    return get_client().request('DELETE', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a single view of a project.', examples=['load_tool("vikunja.get_view")(1, 1)'], tool_class='read', aliases=[])
def get_view(project_id: int, view_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns one view of a project. The view must belong to the project in the path. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    return get_client().request('GET', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a view of a project. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_view")(1, 1, {})'], tool_class='write', aliases=[])
def replace_view(project_id: int, view_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces a project view's fields. The view must belong to the project in the path, and only project admins may update it. Use PATCH for a partial update."
    return get_client().request('PUT', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='List the buckets of a kanban view.', examples=['load_tool("vikunja.list_buckets")(1, 1)'], tool_class='read', aliases=[])
def list_buckets(project_id: int, view_id: int, page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns all kanban buckets of a project view, ordered by position. Requires read access to the project. The list is not paginated by the server but is returned in the standard list envelope. To get the buckets together with their tasks, use the buckets/tasks endpoint instead.'
    return get_client().page(f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/buckets', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a bucket in a kanban view.', examples=['load_tool("vikunja.create_bucket")(1, 1, \'Nexus integration test\')'], tool_class='write', aliases=[])
def create_bucket(project_id: int, view_id: int, title: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'Creates a kanban bucket in the given project view. The project and view come from the URL, not the body. Requires write access to the project.'
    return get_client().request('POST', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/buckets', params=params, body=fields_body(title, fields))


@register_tool(namespace="vikunja", description='Delete a bucket of a kanban view.', examples=['load_tool("vikunja.delete_bucket")(1, 1, 1)'], tool_class='destructive', aliases=[])
def delete_bucket(project_id: int, view_id: int, bucket_id: int, params: dict[str, Any] | None = None) -> Any:
    "Deletes a kanban bucket and moves its tasks to the view's default bucket; no tasks are deleted. You cannot delete the last bucket of a view (rejected with 412). Requires write access to the project."
    return get_client().request('DELETE', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/buckets/{positive_id(bucket_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a bucket of a kanban view. Full replacement, omitted fields can reset.', examples=['load_tool("vikunja.replace_bucket")(1, 1, 1, {})'], tool_class='write', aliases=[])
def replace_bucket(project_id: int, view_id: int, bucket_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Full replacement. Supply all writable fields or omitted fields may reset. Prefer update tools where available. Replaces a kanban bucket's title, limit and position. The bucket is identified by the URL, which also scopes it to the project and view. Requires write access to the project."
    return get_client().request('PUT', f'projects/{positive_id(project_id)}/views/{positive_id(view_id)}/buckets/{positive_id(bucket_id)}', params=params, body=fields)
