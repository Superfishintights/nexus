"""SABnzbd general API wrapper tools."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="sabnzbd",
    name="call",
    description="Call a raw SABnzbd API mode with optional query parameters.",
    examples=["sabnzbd.call('queue', {'limit': 10})", "sabnzbd.call('version', include_api_key=False)"],
)
def call(
    mode: str,
    params: Optional[Mapping[str, Any]] = None,
    *,
    include_api_key: bool = True,
    output: Optional[str] = "json",
) -> Any:
    return get_client().call(mode, params, include_api_key=include_api_key, output=output)


@register_tool(
    namespace="sabnzbd",
    name="get_version",
    description="Get the version of the running SABnzbd instance.",
    examples=["sabnzbd.get_version()"],
)
def get_version() -> Dict[str, Any]:
    data = get_client().call("version", include_api_key=False)
    return data if isinstance(data, dict) else {"version": data}


@register_tool(
    namespace="sabnzbd",
    name="get_auth",
    description="Get SABnzbd authentication methods available for API interaction.",
    examples=["sabnzbd.get_auth()"],
)
def get_auth() -> Dict[str, Any]:
    data = get_client().call("auth", include_api_key=False)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="shutdown",
    description="Shutdown the running SABnzbd process.",
    examples=["sabnzbd.shutdown()"],
)
def shutdown() -> Dict[str, Any]:
    data = get_client().call("shutdown")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="restart",
    description="Restart the running SABnzbd process.",
    examples=["sabnzbd.restart()"],
)
def restart() -> Dict[str, Any]:
    data = get_client().call("restart")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="restart_repair",
    description="Restart SABnzbd and perform a queue repair.",
    examples=["sabnzbd.restart_repair()"],
)
def restart_repair() -> Dict[str, Any]:
    data = get_client().call("restart_repair")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="pause_post_processing",
    description="Pause the SABnzbd post-processing queue.",
    examples=["sabnzbd.pause_post_processing()"],
)
def pause_post_processing() -> Dict[str, Any]:
    data = get_client().call("pause_pp")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="resume_post_processing",
    description="Resume the SABnzbd post-processing queue.",
    examples=["sabnzbd.resume_post_processing()"],
)
def resume_post_processing() -> Dict[str, Any]:
    data = get_client().call("resume_pp")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="fetch_rss_now",
    description="Fetch and process all SABnzbd RSS feeds immediately.",
    examples=["sabnzbd.fetch_rss_now()"],
)
def fetch_rss_now() -> Dict[str, Any]:
    data = get_client().call("rss_now")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="scan_watched_now",
    description="Scan the SABnzbd watched folder immediately.",
    examples=["sabnzbd.scan_watched_now()"],
)
def scan_watched_now() -> Dict[str, Any]:
    data = get_client().call("watched_now")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="reset_quota",
    description="Reset the user-defined SABnzbd quota to zero.",
    examples=["sabnzbd.reset_quota()"],
)
def reset_quota() -> Dict[str, Any]:
    data = get_client().call("reset_quota")
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="translate",
    description="Translate SABnzbd UI text from English to the user's configured locale.",
    examples=["sabnzbd.translate('Watched Folder')"],
)
def translate(text: str) -> Dict[str, Any]:
    data = get_client().call("translate", {"value": text})
    return data if isinstance(data, dict) else {"value": data}
