"""SABnzbd configuration and maintenance tools."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

from nexus.tool_registry import register_tool

from .client import csv, get_client


@register_tool(
    namespace="sabnzbd",
    name="get_categories",
    description="Get all SABnzbd categories.",
    examples=["sabnzbd.get_categories()"],
)
def get_categories() -> Dict[str, Any]:
    data = get_client().call("get_cats")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="get_scripts",
    description="Get all SABnzbd post-processing scripts.",
    examples=["sabnzbd.get_scripts()"],
)
def get_scripts() -> Dict[str, Any]:
    data = get_client().call("get_scripts")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="get_server_stats",
    description="Get SABnzbd download statistics in bytes, total and per server.",
    examples=["sabnzbd.get_server_stats()"],
)
def get_server_stats() -> Dict[str, Any]:
    data = get_client().call("server_stats")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="delete_config_item",
    description="Delete a SABnzbd configuration item within servers, rss, categories, or sorters.",
    examples=["sabnzbd.delete_config_item('servers', 'ServerName')"],
)
def delete_config_item(section: str, keyword: str) -> Dict[str, Any]:
    data = get_client().call("del_config", {"section": section, "keyword": keyword})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="get_config",
    description="Get the SABnzbd configuration, a config section, or one item by section and keyword.",
    examples=["sabnzbd.get_config()", "sabnzbd.get_config(section='servers', keyword='ServerName')"],
)
def get_config(*, section: Optional[str] = None, keyword: Optional[str] = None) -> Dict[str, Any]:
    data = get_client().call("get_config", {"section": section, "keyword": keyword})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="set_config",
    description="Set a SABnzbd configuration value or update a named server, rss, category, or sorter item.",
    examples=["sabnzbd.set_config('misc', keyword='cleanup_list', value='.sfv,.nzb')", "sabnzbd.set_config('categories', name='tv', values={'dir': 'TV'})"],
)
def set_config(
    section: str,
    *,
    keyword: Optional[str] = None,
    value: Optional[Any] = None,
    name: Optional[str] = None,
    values: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"section": section, "keyword": keyword, "value": value, "name": name}
    if values:
        params.update(dict(values))
    data = get_client().call("set_config", params)
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="set_config_default",
    description="Reset one or more SABnzbd misc config settings to their default values.",
    examples=["sabnzbd.set_config_default('cleanup_list')", "sabnzbd.set_config_default(['cleanup_list', 'queue_complete'])"],
)
def set_config_default(keyword: str | Iterable[str]) -> Dict[str, Any]:
    data = get_client().call("set_config_default", {"keyword": csv(keyword)})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="reset_api_key",
    description="Reset the SABnzbd API key and return the new key.",
    examples=["sabnzbd.reset_api_key()"],
)
def reset_api_key() -> Dict[str, Any]:
    data = get_client().call("config", {"name": "set_apikey"})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="reset_nzb_key",
    description="Reset the SABnzbd NZB key and return the new key.",
    examples=["sabnzbd.reset_nzb_key()"],
)
def reset_nzb_key() -> Dict[str, Any]:
    data = get_client().call("config", {"name": "set_nzbkey"})
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="regenerate_certs",
    description="Regenerate SABnzbd self-signed HTTPS certificates; restart is required for the new certificates to take effect.",
    examples=["sabnzbd.regenerate_certs()"],
)
def regenerate_certs() -> Dict[str, Any]:
    data = get_client().call("config", {"name": "regenerate_certs"})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="get_warnings",
    description="Get all active SABnzbd warnings.",
    examples=["sabnzbd.get_warnings()"],
)
def get_warnings() -> Dict[str, Any]:
    data = get_client().call("warnings")
    return data if isinstance(data, dict) else {"data": data}


@register_tool(
    namespace="sabnzbd",
    name="clear_warnings",
    description="Clear all active SABnzbd warnings.",
    examples=["sabnzbd.clear_warnings()"],
)
def clear_warnings() -> Dict[str, Any]:
    data = get_client().call("warnings", {"name": "clear"})
    return data if isinstance(data, dict) else {"status": data}


@register_tool(
    namespace="sabnzbd",
    name="show_log",
    description="Get SABnzbd's anonymized log download response as text or binary-decoded text when available.",
    examples=["sabnzbd.show_log()"],
)
def show_log() -> Dict[str, Any]:
    data = get_client().call("showlog", output=None)
    return data if isinstance(data, dict) else {"data": data}
