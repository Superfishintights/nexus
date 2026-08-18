"""SABnzbd history tools."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from nexus.tool_registry import register_tool

from .client import csv, get_client


@register_tool(
    namespace="sabnzbd",
    name="get_history",
    description="Get SABnzbd history, optionally filtered by category, status, search text, nzo ids, archive state, or failed-only.",
    examples=["sabnzbd.get_history(limit=20)", "sabnzbd.get_history(failed_only=True)"],
)
def get_history(
    *,
    start: Optional[int] = None,
    limit: Optional[int] = None,
    archive: Optional[bool] = None,
    cat: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    nzo_ids: Optional[str | Iterable[str]] = None,
    failed_only: Optional[bool] = None,
    last_history_update: Optional[int] = None,
) -> Dict[str, Any]:
    params = {
        "start": start,
        "limit": limit,
        "archive": archive,
        "cat": cat,
        "status": status,
        "search": search,
        "nzo_ids": csv(nzo_ids) if nzo_ids is not None else None,
        "failed_only": failed_only,
        "last_history_update": last_history_update,
    }
    data = get_client().call("history", params)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="retry_history_item",
    description="Retry one or more failed SABnzbd history items; can include a password and optional supplemental NZB upload.",
    examples=["sabnzbd.retry_history_item('SABnzbd_nzo_abc123')", "sabnzbd.retry_history_item(['SABnzbd_nzo_a'], password='secret')"],
)
def retry_history_item(
    nzo_ids: str | Iterable[str],
    *,
    password: Optional[str] = None,
    nzb_file_path: Optional[str] = None,
) -> Dict[str, Any]:
    params = {"value": csv(nzo_ids), "password": password}
    if nzb_file_path:
        data = get_client().upload_file("retry", nzb_file_path, params)
    else:
        data = get_client().call("retry", params)
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="retry_all_history",
    description="Retry all failed SABnzbd history items.",
    examples=["sabnzbd.retry_all_history()"],
)
def retry_all_history() -> Dict[str, Any]:
    data = get_client().call("retry_all")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="delete_history_items",
    description="Delete or archive SABnzbd history items by nzo id, multiple ids, 'all', or 'failed'; optionally delete failed files.",
    examples=["sabnzbd.delete_history_items('failed', archive=False, del_files=True)"],
)
def delete_history_items(
    nzo_ids: str | Iterable[str],
    *,
    archive: Optional[bool] = None,
    del_files: bool = False,
) -> Dict[str, Any]:
    data = get_client().call(
        "history",
        {
            "name": "delete",
            "value": csv(nzo_ids),
            "archive": archive,
            "del_files": del_files,
        },
    )
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="mark_history_completed",
    description="Mark failed SABnzbd history items as completed; this removes associated incomplete download files.",
    examples=["sabnzbd.mark_history_completed(['SABnzbd_nzo_a', 'SABnzbd_nzo_b'])"],
)
def mark_history_completed(nzo_ids: str | Iterable[str]) -> Dict[str, Any]:
    data = get_client().call("history", {"name": "mark_as_completed", "value": csv(nzo_ids)})
    return data if isinstance(data, dict) else {"status": data}
