"""SABnzbd status tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="sabnzbd",
    name="get_status",
    description="Get SABnzbd status information, including server and orphan details.",
    examples=["sabnzbd.get_status(skip_dashboard=True)", "sabnzbd.get_status(calculate_performance=True)"],
)
def get_status(
    *,
    skip_dashboard: Optional[bool] = None,
    calculate_performance: Optional[bool] = None,
) -> Dict[str, Any]:
    data = get_client().call(
        "status",
        {
            "skip_dashboard": skip_dashboard,
            "calculate_performance": calculate_performance,
        },
    )
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="get_fullstatus",
    description="Get SABnzbd fullstatus output for compatibility with older SABnzbd versions.",
    examples=["sabnzbd.get_fullstatus()"],
)
def get_fullstatus() -> Dict[str, Any]:
    data = get_client().call("fullstatus")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="unblock_server",
    description="Unblock a SABnzbd server by server name.",
    examples=["sabnzbd.unblock_server('Frugal')"],
)
def unblock_server(server_name: str) -> Dict[str, Any]:
    data = get_client().call("status", {"name": "unblock_server", "value": server_name})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="delete_orphan",
    description="Delete one orphaned SABnzbd job folder from the incomplete folder.",
    examples=["sabnzbd.delete_orphan('Lost.Folder.BRRip.x264.1080p')"],
)
def delete_orphan(folder_name: str) -> Dict[str, Any]:
    data = get_client().call("status", {"name": "delete_orphan", "value": folder_name})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="delete_all_orphans",
    description="Delete all orphaned SABnzbd job folders from the incomplete folder.",
    examples=["sabnzbd.delete_all_orphans()"],
)
def delete_all_orphans() -> Dict[str, Any]:
    data = get_client().call("status", {"name": "delete_all_orphan"})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="retry_orphan",
    description="Retry one orphaned SABnzbd job folder.",
    examples=["sabnzbd.retry_orphan('Lost.Folder.BRRip.x264.1080p')"],
)
def retry_orphan(folder_name: str) -> Dict[str, Any]:
    data = get_client().call("status", {"name": "add_orphan", "value": folder_name})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="retry_all_orphans",
    description="Retry all orphaned SABnzbd job folders.",
    examples=["sabnzbd.retry_all_orphans()"],
)
def retry_all_orphans() -> Dict[str, Any]:
    data = get_client().call("status", {"name": "add_all_orphan"})
    return data if isinstance(data, dict) else {"status": data}
