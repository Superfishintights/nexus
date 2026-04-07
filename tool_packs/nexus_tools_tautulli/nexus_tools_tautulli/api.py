"""Tautulli API wrapper tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="tautulli",
    name="call",
    aliases=["tautulli_call"],
    description="Call a raw Tautulli API command and return the `response.data` payload.",
    examples=[
        "tautulli.call('get_activity')",
        "tautulli.call('get_history', {'length': 5})",
    ],
)
def tautulli_call(cmd: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Call a raw Tautulli API command.

    Args:
        cmd: Tautulli API command (e.g., 'get_activity').
        params: Optional command parameters (dict).
    """
    return get_client().call(cmd, params=params)


@register_tool(
    namespace="tautulli",
    name="get_activity",
    aliases=["tautulli_get_activity"],
    description="Get current Plex activity from Tautulli.",
    examples=["tautulli.get_activity()"],
)
def tautulli_get_activity() -> Dict[str, Any]:
    """Get current Plex activity from Tautulli."""
    data = get_client().call("get_activity")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="tautulli",
    name="get_libraries",
    aliases=["tautulli_get_libraries"],
    description="List Plex libraries known to Tautulli.",
    examples=["tautulli.get_libraries()"],
)
def tautulli_get_libraries() -> Dict[str, Any]:
    """List Plex libraries known to Tautulli."""
    data = get_client().call("get_libraries")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="tautulli",
    name="get_library_names",
    aliases=["tautulli_get_library_names"],
    description="Get Plex library names (name/id/type) from Tautulli.",
    examples=["tautulli.get_library_names()"],
)
def tautulli_get_library_names() -> List[Dict[str, Any]]:
    """Get Plex library names (name/id/type) from Tautulli."""
    libraries = get_client().call("get_libraries")
    if not isinstance(libraries, dict):
        return [{"data": libraries}]
    sections = libraries.get("sections") or []
    result: List[Dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        result.append(
            {
                "section_id": section.get("section_id"),
                "section_name": section.get("section_name"),
                "section_type": section.get("section_type"),
                "agent": section.get("agent"),
            }
        )
    return result


@register_tool(
    namespace="tautulli",
    name="get_users",
    aliases=["tautulli_get_users"],
    description="List users known to Tautulli.",
    examples=["tautulli.get_users()"],
)
def tautulli_get_users() -> Dict[str, Any]:
    """List users known to Tautulli."""
    data = get_client().call("get_users")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="tautulli",
    name="get_server_info",
    aliases=["tautulli_get_server_info"],
    description="Get Tautulli server info.",
    examples=["tautulli.get_server_info()"],
)
def tautulli_get_server_info() -> Dict[str, Any]:
    """Get Tautulli server info."""
    data = get_client().call("get_server_info")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="tautulli",
    name="get_history",
    aliases=["tautulli_get_history"],
    description="Get playback history from Tautulli.",
    examples=["tautulli.get_history(length=10)", "tautulli.get_history(user='alice', length=5)"],
)
def tautulli_get_history(
    *,
    user: Optional[str] = None,
    user_id: Optional[int] = None,
    rating_key: Optional[int] = None,
    section_id: Optional[int] = None,
    media_type: Optional[str] = None,
    length: int = 25,
    start: int = 0,
    order_column: Optional[str] = None,
    order_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Get playback history from Tautulli."""
    params: Dict[str, Any] = {
        "user": user,
        "user_id": user_id,
        "rating_key": rating_key,
        "section_id": section_id,
        "media_type": media_type,
        "length": length,
        "start": start,
        "order_column": order_column,
        "order_dir": order_dir,
    }
    data = get_client().call("get_history", params=params)
    return data if isinstance(data, dict) else {"data": data}
