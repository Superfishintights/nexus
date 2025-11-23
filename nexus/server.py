#!/usr/bin/env python3
"""
Nexus MCP Server

A Model Context Protocol server that exposes a single code execution entrypoint.
The model writes Python code that imports and calls tool functions from any domain.
Supports: Jira, Confluence, GitLab, Jenkins, Talos, and any other tools in the tools/ directory.
"""

import json
import sys
import os

sys.path.insert(0, '/home/jaymillington/development/ai')

try:
    from fastmcp import FastMCP
except ImportError:
    print("Error: fastmcp is required. Install with: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

from nexus.runner import run_user_code, RunnerExecutionError
from nexus.tool_registry import iter_tools

mcp = FastMCP("Nexus MCP Server")


@mcp.tool()
def run_code(code: str) -> str:
    """
    Execute Python code that imports and calls tool functions from any domain.

    The code can import tools from tools.jira, tools.confluence, tools.gitlab, etc.
    and must set RESULT to the final value. Available tools are automatically
    registered and can be discovered via the TOOLS global variable.

    Examples:
        # Jira
        from tools.jira.search_issues import search_issues
        results = search_issues('project = PROJ AND status = Open', max_results=5)
        RESULT = [r['key'] for r in results['issues']]

        # Multiple domains
        from tools.jira.get_issue_details import get_issue_details
        from tools.confluence.search_pages import search_pages
        issue = get_issue_details('PROJ-123')
        pages = search_pages(issue['summary'])
        RESULT = {'issue': issue, 'related_pages': pages}

    Args:
        code: The Python source code to execute

    Returns:
        JSON string containing the execution result, logs, and available tools
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
def list_available_tools() -> str:
    """
    List all available tools from all domains that can be imported and called in code.
    Includes tools from Jira, Confluence, GitLab, and any other configured domains.

    Returns:
        JSON string containing tool metadata (name, module, description)
    """
    tools = []
    for tool in iter_tools():
        tools.append({
            'name': tool.name,
            'module': tool.module,
            'description': tool.description,
        })

    response = {
        'totalTools': len(tools),
        'tools': tools,
    }

    return json.dumps(response, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
