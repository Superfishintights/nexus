"""Ordinary Vikunja API v2 operations from the checked live specification."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import get_client, positive_id, path_text, fields_body


@register_tool(namespace="vikunja", description='List teams.', examples=['load_tool("vikunja.list_teams")()'], tool_class='read', aliases=[])
def list_teams(page: int = 1, per_page: int = 50, query: str | None = None, params: dict[str, Any] | None = None) -> Any:
    'Returns the teams the authenticated user is a member of, paginated. Set include_public=true to also surface public teams the user is not a member of, where the instance has public teams enabled.'
    return get_client().page('teams', page=page, per_page=per_page, params={**(params or {}), **({"q": query} if query is not None else {})})


@register_tool(namespace="vikunja", description='Create a team.', examples=['load_tool("vikunja.create_team")(\'Planning\')'], tool_class='write', aliases=[])
def create_team(name: str, fields: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    'Creates a team; the authenticated user becomes its first member and an admin of it.'
    if not isinstance(name, str) or not name.strip():
        raise ValueError('name must be nonempty')
    return get_client().request('POST', 'teams', params=params, body={**(fields or {}), 'name': name})


@register_tool(namespace="vikunja", description='Delete a team.', examples=['load_tool("vikunja.delete_team")(1)'], tool_class='destructive', aliases=[])
def delete_team(team_id: int, params: dict[str, Any] | None = None) -> Any:
    'Deletes a team and revokes the access it granted to all of its members. Only a team admin may delete it.'
    return get_client().request('DELETE', f'teams/{positive_id(team_id)}', params=params)


@register_tool(namespace="vikunja", description='Get a team.', examples=['load_tool("vikunja.get_team")(1)'], tool_class='read', aliases=[])
def get_team(team_id: int, params: dict[str, Any] | None = None) -> Any:
    'Returns a single team the user is a member of. Sends an ETag; pass it as If-None-Match on a later read to get a 304 Not Modified.'
    return get_client().request('GET', f'teams/{positive_id(team_id)}', params=params)


@register_tool(namespace="vikunja", description='Update a team. Full replacement, omitted fields may reset.', examples=['load_tool("vikunja.replace_team")(1, {})'], tool_class='write', aliases=[])
def replace_team(team_id: int, fields: dict[str, Any], params: dict[str, Any] | None = None) -> Any:
    "Replaces a team's fields — only a team admin may update it. Use PATCH for a partial update."
    return get_client().request('PUT', f'teams/{positive_id(team_id)}', params=params, body=fields)


@register_tool(namespace="vikunja", description='Add a member to a team.', examples=['load_tool("vikunja.add_team_member")(1, \'member\')'], tool_class='write', aliases=[])
def add_team_member(team_id: int, username: str, admin: bool = False, params: dict[str, Any] | None = None) -> Any:
    'Adds a user to a team by username. Only a team admin may add members.'
    path_text(username)
    if not isinstance(admin, bool):
        raise ValueError('admin must be boolean')
    return get_client().request('POST', f'teams/{positive_id(team_id)}/members', params=params, body={'username': username, 'admin': admin})


@register_tool(namespace="vikunja", description='Remove a member from a team.', examples=['load_tool("vikunja.remove_team_member")(1, \'member\')'], tool_class='destructive', aliases=[])
def remove_team_member(team_id: int, username: str, params: dict[str, Any] | None = None) -> Any:
    'Removes a user from a team, revoking the access the team granted them. A team admin may remove anyone; a member may remove themselves. The last member of a team cannot be removed.'
    return get_client().request('DELETE', f'teams/{positive_id(team_id)}/members/{path_text(username)}', params=params)


@register_tool(namespace="vikunja", description="Toggle a team member's admin status.", examples=['load_tool("vikunja.toggle_team_member_admin")(1, \'member\')'], tool_class='admin', aliases=[])
def toggle_team_member_admin(team_id: int, username: str, params: dict[str, Any] | None = None) -> Any:
    "Flips the member's admin flag: an admin becomes a regular member and vice-versa. The request body is ignored. Only a team admin may do this."
    return get_client().request('POST', f'teams/{positive_id(team_id)}/members/{path_text(username)}/admin', params=params)


@register_tool(namespace="vikunja", description="Partially update a team without replacing unmentioned fields.", examples=['load_tool("vikunja.update_team")(1, {"name": "Planning"})'], tool_class="write", aliases=[])
def update_team(team_id: int, fields: dict[str, Any]) -> Any:
    return get_client().request("PATCH", f"teams/{positive_id(team_id)}", body=fields)
