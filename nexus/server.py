#!/usr/bin/env python3
"""
Nexus MCP Server

A Model Context Protocol server that exposes a small, context-efficient surface:
`run_code`, `search_tools`, and `get_tool`.

The model writes Python code that imports and calls tool functions from any
configured tool package.
"""

import json
import sys
from typing import Any, Dict, List

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: fastmcp is required. Install with: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

from nexus.runner import run_user_code, RunnerExecutionError
from nexus.tool_catalog import get_catalog, search_catalog, spec_to_dict, ToolSpec
from nexus.tool_registry import get_tool as get_loaded_tool, is_tool_loaded

mcp = FastMCP("Nexus MCP Server")


@mcp.tool()
def run_code(code: str) -> str:
    """
    Execute Python code that imports and calls tool functions from any domain.

    The code can import tools from configured packages (default: tools.*)
    and must set RESULT to the final value. Available tools can be discovered
    via the search_tools/get_tool MCP endpoints or through the TOOLS global
    (a lazy catalog) within the execution environment.

    Examples:
        # Discover tools and call one lazily.
        # (Model would typically call search_tools/get_tool first.)
        issue_status = load_tool("get_issue_status")
        RESULT = issue_status("PROJ-123")

    Args:
        code: The Python source code to execute

    Returns:
        JSON string containing the execution result and logs
    """
    try:
        result = run_user_code(code)

        response = {
            'success': True,
            'result': result.result,
            'logs': result.logs,
        }

        return json.dumps(response, indent=2, ensure_ascii=False)

    except RunnerExecutionError as e:
        error_response = {
            'success': False,
            'error': 'Code execution failed',
            'details': str(e),
        }
        return json.dumps(error_response, indent=2)
    except Exception as e:
        error_response = {
            'success': False,
            'error': 'Unexpected error',
            'details': str(e),
        }
        return json.dumps(error_response, indent=2)


@mcp.tool()
def search_tools(
    query: str = "",
    detail_level: str = "summary",
    limit: int = 20,
) -> str:
    """Search for relevant tools without loading every definition.

    Args:
        query: Free-text search query. Empty means "list tools".
        detail_level: One of "name", "summary", "full".
        limit: Maximum number of tools to return.

    Returns:
        JSON string containing matching tool metadata.
    """

    matches = search_catalog(query, limit=limit)
    tools: List[Dict[str, Any]] = [
        _tool_to_dict(spec, detail_level=detail_level) for spec in matches
    ]

    response = {
        "success": True,
        "query": query,
        "detailLevel": detail_level,
        "totalMatches": len(matches),
        "tools": tools,
    }
    return json.dumps(response, indent=2, ensure_ascii=False)


@mcp.tool()
def get_tool(name: str, detail_level: str = "full") -> str:
    """Return metadata for a single tool by name.

    Args:
        name: Registered tool name (e.g., "get_issue_status").
        detail_level: One of "name", "summary", "full".

    Returns:
        JSON string with tool metadata or an error if not found.
    """

    catalog = get_catalog()
    spec = catalog.get(name)
    if spec is not None:
        response = {
            "success": True,
            "tool": _tool_to_dict(spec, detail_level=detail_level),
        }
        return json.dumps(response, indent=2, ensure_ascii=False)

    if is_tool_loaded(name):
        info = get_loaded_tool(name)
        response = {
            "success": True,
            "tool": _tool_info_to_dict(info, detail_level=detail_level),
        }
        return json.dumps(response, indent=2, ensure_ascii=False)

    error_response = {
        "success": False,
        "error": "Unknown tool",
        "name": name,
    }
    return json.dumps(error_response, indent=2, ensure_ascii=False)


@mcp.tool()
def list_available_tools() -> str:
    """Deprecated: use search_tools instead."""

    return search_tools("", detail_level="name", limit=10_000)


def _tool_to_dict(spec: ToolSpec, *, detail_level: str) -> Dict[str, Any]:
    loaded = is_tool_loaded(spec.name)
    tool_dict = spec_to_dict(spec, detail_level=detail_level, loaded=loaded)

    if loaded and detail_level != "name":
        info = get_loaded_tool(spec.name)
        tool_dict["module"] = info.module
        tool_dict["signature"] = info.signature
        if detail_level == "summary":
            tool_dict["description"] = info.description.splitlines()[0] if info.description else ""
        else:
            tool_dict["description"] = info.description
            tool_dict["examples"] = list(info.examples)

    return tool_dict


def _tool_info_to_dict(info, *, detail_level: str) -> Dict[str, Any]:
    base: Dict[str, Any] = {"name": info.name, "module": info.module}
    if detail_level == "name":
        return base
    base.update(
        {
            "description": info.description.splitlines()[0] if info.description else "",
            "signature": info.signature,
            "loaded": True,
        }
    )
    if detail_level == "full":
        base["description"] = info.description
        base["examples"] = list(info.examples)
    return base


if __name__ == "__main__":
    mcp.run()
