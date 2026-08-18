"""SABnzbd queue tools."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from nexus.tool_registry import register_tool

from .client import csv, get_client, nzb_options


@register_tool(
    namespace="sabnzbd",
    name="get_queue",
    description="Get the full SABnzbd queue, optionally filtered by category, priority, status, search text, or nzo ids.",
    examples=["sabnzbd.get_queue(limit=10)", "sabnzbd.get_queue(status='Paused')"],
)
def get_queue(
    *,
    start: Optional[int] = None,
    limit: Optional[int] = None,
    cat: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    nzo_ids: Optional[str | Iterable[str]] = None,
) -> Dict[str, Any]:
    params = {
        "start": start,
        "limit": limit,
        "cat": cat,
        "priority": priority,
        "status": status,
        "search": search,
        "nzo_ids": csv(nzo_ids) if nzo_ids is not None else None,
    }
    data = get_client().call("queue", params)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="pause_queue",
    description="Pause the entire SABnzbd queue globally.",
    examples=["sabnzbd.pause_queue()"],
)
def pause_queue() -> Dict[str, Any]:
    data = get_client().call("pause")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="resume_queue",
    description="Resume the entire SABnzbd queue globally.",
    examples=["sabnzbd.resume_queue()"],
)
def resume_queue() -> Dict[str, Any]:
    data = get_client().call("resume")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="set_pause_timer",
    description="Pause the entire SABnzbd queue for a number of minutes.",
    examples=["sabnzbd.set_pause_timer(50)"],
)
def set_pause_timer(minutes: int) -> Dict[str, Any]:
    data = get_client().call("config", {"name": "set_pause", "value": minutes})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="set_speedlimit",
    description="Set SABnzbd speed limit as a percentage or absolute value such as '400K' or '4M'.",
    examples=["sabnzbd.set_speedlimit('30')", "sabnzbd.set_speedlimit('400K')"],
)
def set_speedlimit(value: str) -> Dict[str, Any]:
    data = get_client().call("config", {"name": "speedlimit", "value": value})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="change_complete_action",
    description="Change the action SABnzbd performs when the queue completes, such as shutdown_program or script_NAME.",
    examples=["sabnzbd.change_complete_action('shutdown_program')"],
)
def change_complete_action(action: str) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "change_complete_action", "value": action})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="sort_queue",
    description="Sort the SABnzbd queue by avg_age, name, remaining, or size in asc or desc order.",
    examples=["sabnzbd.sort_queue('avg_age', 'desc')"],
)
def sort_queue(sort: str, direction: str = "asc") -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "sort", "sort": sort, "dir": direction})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="add_url",
    description="Add an NZB to SABnzbd by URL and return the created nzo ids.",
    examples=["sabnzbd.add_url('https://indexer.example/get.php?id=123', cat='tv')"],
)
def add_url(
    url: str,
    *,
    nzbname: Optional[str] = None,
    password: Optional[str] = None,
    cat: Optional[str] = None,
    script: Optional[str] = None,
    priority: Optional[int] = None,
    pp: Optional[int] = None,
) -> Dict[str, Any]:
    params = {"name": url}
    params.update(nzb_options(nzbname=nzbname, password=password, cat=cat, script=script, priority=priority, pp=pp))
    data = get_client().call("addurl", params)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="add_file",
    description="Upload a local NZB file to SABnzbd and add it to the queue.",
    examples=["sabnzbd.add_file('/downloads/show.nzb', cat='tv')"],
)
def add_file(
    file_path: str,
    *,
    nzbname: Optional[str] = None,
    password: Optional[str] = None,
    cat: Optional[str] = None,
    script: Optional[str] = None,
    priority: Optional[int] = None,
    pp: Optional[int] = None,
) -> Dict[str, Any]:
    params = nzb_options(nzbname=nzbname, password=password, cat=cat, script=script, priority=priority, pp=pp)
    data = get_client().upload_file("addfile", file_path, params)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="add_local_file",
    description="Add an NZB by a filesystem path that the SABnzbd server can access.",
    examples=["sabnzbd.add_local_file('/watch/movie.nzb', cat='movies')"],
)
def add_local_file(
    path: str,
    *,
    nzbname: Optional[str] = None,
    password: Optional[str] = None,
    cat: Optional[str] = None,
    script: Optional[str] = None,
    priority: Optional[int] = None,
    pp: Optional[int] = None,
) -> Dict[str, Any]:
    params = {"name": path}
    params.update(nzb_options(nzbname=nzbname, password=password, cat=cat, script=script, priority=priority, pp=pp))
    data = get_client().call("addlocalfile", params)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="pause_job",
    description="Pause one SABnzbd queue job by nzo id.",
    examples=["sabnzbd.pause_job('SABnzbd_nzo_abc123')"],
)
def pause_job(nzo_id: str) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "pause", "value": nzo_id})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="resume_job",
    description="Resume one SABnzbd queue job by nzo id.",
    examples=["sabnzbd.resume_job('SABnzbd_nzo_abc123')"],
)
def resume_job(nzo_id: str) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "resume", "value": nzo_id})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="delete_jobs",
    description="Delete SABnzbd queue jobs by nzo id, multiple ids, or 'all'; optionally delete downloaded files.",
    examples=["sabnzbd.delete_jobs(['SABnzbd_nzo_a', 'SABnzbd_nzo_b'], del_files=True)"],
)
def delete_jobs(nzo_ids: str | Iterable[str], *, del_files: bool = False) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "delete", "value": csv(nzo_ids), "del_files": del_files})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="purge_queue",
    description="Remove all SABnzbd queue jobs, or only jobs matching search; optionally delete downloaded files.",
    examples=["sabnzbd.purge_queue(search='sample', del_files=True)"],
)
def purge_queue(*, search: Optional[str] = None, del_files: bool = False) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "purge", "search": search, "del_files": del_files})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="move_job",
    description="Move a SABnzbd queue job above another job or to a numeric queue position.",
    examples=["sabnzbd.move_job('SABnzbd_nzo_a', 'SABnzbd_nzo_b')", "sabnzbd.move_job('SABnzbd_nzo_a', 2)"],
)
def move_job(nzo_id: str, destination: str | int) -> Dict[str, Any]:
    data = get_client().call("switch", {"value": nzo_id, "value2": destination})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="change_job_category",
    description="Change the category of a SABnzbd queue job.",
    examples=["sabnzbd.change_job_category('SABnzbd_nzo_abc123', 'tv')"],
)
def change_job_category(nzo_id: str, category: str) -> Dict[str, Any]:
    data = get_client().call("change_cat", {"value": nzo_id, "value2": category})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="change_job_script",
    description="Change the post-processing script assigned to a SABnzbd queue job.",
    examples=["sabnzbd.change_job_script('SABnzbd_nzo_abc123', 'Notify.py')"],
)
def change_job_script(nzo_id: str, script: str) -> Dict[str, Any]:
    data = get_client().call("change_script", {"value": nzo_id, "value2": script})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="change_job_priority",
    description="Change the priority of a SABnzbd queue job; affects queue position.",
    examples=["sabnzbd.change_job_priority('SABnzbd_nzo_abc123', 1)"],
)
def change_job_priority(nzo_id: str, priority: int) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "priority", "value": nzo_id, "value2": priority})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="change_job_post_processing",
    description="Change post-processing options for a SABnzbd queue job.",
    examples=["sabnzbd.change_job_post_processing('SABnzbd_nzo_abc123', 3)"],
)
def change_job_post_processing(nzo_id: str, pp: int) -> Dict[str, Any]:
    data = get_client().call("change_opts", {"value": nzo_id, "value2": pp})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="rename_job",
    description="Rename a SABnzbd queue job and optionally set its unpack password.",
    examples=["sabnzbd.rename_job('SABnzbd_nzo_abc123', 'New.Name', password='secret')"],
)
def rename_job(nzo_id: str, new_name: str, *, password: Optional[str] = None) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "rename", "value": nzo_id, "value2": new_name, "value3": password})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="get_job_files",
    description="Get the files inside a SABnzbd queue job.",
    examples=["sabnzbd.get_job_files('SABnzbd_nzo_abc123')"],
)
def get_job_files(nzo_id: str) -> Dict[str, Any]:
    data = get_client().call("get_files", {"value": nzo_id})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="move_job_files",
    description="Move files inside a SABnzbd queue job to top, bottom, up, or down.",
    examples=["sabnzbd.move_job_files('SABnzbd_nzo_abc123', ['SABnzbd_nzf_1'], 'top')"],
)
def move_job_files(
    nzo_id: str,
    nzf_ids: str | Iterable[str],
    location: str,
    *,
    size: Optional[int] = None,
) -> Dict[str, Any]:
    data = get_client().call("move_nzf_bulk", {"name": location, "value": nzo_id, "nzf_ids": csv(nzf_ids), "size": size})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="delete_job_files",
    description="Remove files from a SABnzbd queue job by nzf id.",
    examples=["sabnzbd.delete_job_files('SABnzbd_nzo_abc123', ['SABnzbd_nzf_1'])"],
)
def delete_job_files(nzo_id: str, nzf_ids: str | Iterable[str]) -> Dict[str, Any]:
    data = get_client().call("queue", {"name": "delete_nzf", "value": nzo_id, "value2": csv(nzf_ids)})
    return data if isinstance(data, dict) else {"data": data}
