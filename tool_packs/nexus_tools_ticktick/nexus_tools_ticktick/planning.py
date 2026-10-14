"""Bounded account reads and native parent-task updates for planner consumers."""
from __future__ import annotations
from typing import Any
from nexus.tool_registry import register_tool
from .client import TickTickError, get_client, path_id


@register_tool(aliases=[], namespace='ticktick', description='Read projects with supported offset/limit pagination, stopping at a caller-selected maximum.', examples=['load_tool("ticktick.list_all_projects")(page_size=100, max_projects=1000)'])
def list_all_projects(page_size: int = 100, max_projects: int = 1000) -> dict[str, Any]:
    if not 1 <= page_size <= 200 or not 1 <= max_projects <= 10000:
        raise ValueError('page_size must be 1..200; max_projects must be 1..10000')
    client = get_client()
    projects = []
    offset = 0
    while len(projects) < max_projects:
        limit = min(page_size, max_projects-len(projects))
        page = client.get('project', params={'offset':offset,'limit':limit})
        if not isinstance(page, list):
            raise TickTickError('TickTick project listing did not return an array')
        projects.extend(page[:limit])
        offset += len(page)
        if len(page) < limit:
            return {'projects':projects,'complete':True,'next_offset':None}
    # An exact boundary needs one small read to avoid calling a full page complete.
    more = client.get('project', params={'offset':offset,'limit':1})
    if not isinstance(more, list):
        raise TickTickError('TickTick project listing did not return an array')
    return {'projects':projects,'complete':not more,'next_offset':offset if more else None}


@register_tool(aliases=[], namespace='ticktick', description='Set or remove a native TickTick parent task with the documented batch Task schema. This is hierarchy, not a dependency.', examples=['load_tool("ticktick.set_task_parent")("project-id", "child-task-id", "parent-task-id")'])
def set_task_parent(project_id: str, task_id: str, parent_id: str = '') -> Any:
    if parent_id == task_id:
        raise ValueError('A task cannot be its own parent')
    client = get_client()
    # Ensure caller IDs are valid and the existing child belongs to this project.
    child = client.get(f'project/{path_id(project_id)}/task/{path_id(task_id)}')
    if not isinstance(child, dict) or child.get('projectId') != project_id:
        raise ValueError('Child task project does not match')
    if parent_id:
        parent = client.get(f'project/{path_id(project_id)}/task/{path_id(parent_id)}')
        if not isinstance(parent, dict) or parent.get('projectId') != project_id:
            raise ValueError('Parent task must belong to the same project')
    return client.post('task/batch', body={'update':[{'id':task_id,'projectId':project_id,'parentId':parent_id}]})


def _ownership_marker(marker: str) -> str:
    import re
    import uuid
    match = re.fullmatch(r'\[personal-agent:([0-9a-fA-F-]{36})\]', marker)
    if not match:
        raise ValueError('Expected an exact [personal-agent:UUID] ownership marker')
    uuid.UUID(match.group(1))
    return marker


def _has_marker(task: dict[str, Any], marker: str) -> bool:
    return any(isinstance(task.get(field), str) and marker in task[field] for field in ('content','desc'))


@register_tool(aliases=[], namespace='ticktick', description='Find planner-owned tasks by an exact ownership marker in content or desc. Bound project/task scans and report truncation explicitly.', examples=['load_tool("ticktick.find_tasks_by_marker")("[personal-agent:12345678-1234-1234-1234-123456789abc]")'])
def find_tasks_by_marker(marker: str, project_ids: list[str] | None = None, max_projects: int = 100, max_tasks: int = 5000, include_completed: bool = False) -> dict[str, Any]:
    """Scan project data for open tasks. Optionally query completed tasks per project.

    Completed reads cap at 200 per project, with no documented continuation.
    A saturated completed response always sets truncated. Default project
    enumeration covers projects returned by the API. Supply inbox/project IDs
    explicitly if their absence from that listing matters.
    """
    _ownership_marker(marker)
    if not 1 <= max_projects <= 1000 or not 1 <= max_tasks <= 50000:
        raise ValueError('max_projects must be 1..1000; max_tasks must be 1..50000')
    truncated = False
    reasons = []
    if project_ids is None:
        listing = list_all_projects(max_projects=max_projects)
        project_ids = [p['id'] for p in listing['projects']]
        if not listing['complete']:
            truncated = True
            reasons.append('project_scan_limit')
    elif len(project_ids) > max_projects:
        project_ids = project_ids[:max_projects]
        truncated = True
        reasons.append('project_scan_limit')
    client = get_client()
    matches = []
    seen = set()
    scanned = 0
    scanned_projects = []
    stop = False
    for project_id in project_ids:
        data = client.get(f'project/{path_id(project_id)}/data')
        if not isinstance(data, dict) or not isinstance(data.get('tasks'), list):
            raise TickTickError('TickTick project data did not return a tasks array')
        arrays = [data['tasks']]
        if include_completed:
            completed = client.post('task/completed', body={'projectIds':[project_id]})
            if not isinstance(completed, list):
                raise TickTickError('TickTick completed task listing did not return an array')
            if len(completed) >= 200:
                truncated = True
                reasons.append('completed_response_cap:'+project_id)
            arrays.append(completed)
        scanned_projects.append(project_id)
        for tasks in arrays:
            for task in tasks:
                if scanned >= max_tasks:
                    truncated = True
                    reasons.append('task_scan_limit')
                    stop = True
                    break
                scanned += 1
                if isinstance(task, dict) and _has_marker(task, marker) and (task.get('projectId'),task.get('id')) not in seen:
                    matches.append(task)
                    seen.add((task.get('projectId'),task.get('id')))
            if stop:
                break
        if stop:
            break
    return {'tasks':matches,'truncated':truncated,'complete':not truncated,'reasons':list(dict.fromkeys(reasons)),'scanned_tasks':scanned,'scanned_project_ids':scanned_projects,'includes_completed':include_completed}


@register_tool(aliases=[], tool_class='destructive', namespace='ticktick', description='Delete a task only when its freshly fetched content or desc contains the exact planner ownership marker.', examples=['load_tool("ticktick.cancel_task")("project-id", "task-id", "[personal-agent:12345678-1234-1234-1234-123456789abc]")'])
def cancel_task(project_id: str, task_id: str, marker: str) -> dict[str, Any]:
    _ownership_marker(marker)
    client = get_client()
    endpoint = f'project/{path_id(project_id)}/task/{path_id(task_id)}'
    task = client.get(endpoint)
    if not isinstance(task, dict) or task.get('id') != task_id or task.get('projectId') != project_id or not _has_marker(task, marker):
        raise ValueError('Refusing cancellation because the fresh task does not match its IDs and ownership marker')
    client.delete(endpoint)
    return {'deleted':True,'project_id':project_id,'task_id':task_id}
