#!/usr/bin/env python3
"""
Example script demonstrating direct usage of the nexus runner.
This bypasses the MCP server and directly calls run_user_code.
"""

import sys
import os

sys.path.insert(0, '/home/jaymillington/development/ai')

from nexus.runner import run_user_code, RunnerExecutionError
from nexus.tool_registry import iter_tools

def main():
    print("=== Nexus Runner Test ===\n")

    # List available tools
    print("Available tools:")
    for tool in iter_tools():
        print(f"  - {tool.name} ({tool.module})")
        print(f"    {tool.description[:80]}...")
    print()

    # Example 1: List available tools from within executed code
    print("Example 1: Discover tools from code")
    code1 = """
tools_list = []
for name, tool_info in TOOLS.items():
    tools_list.append({
        'name': name,
        'module': tool_info.module,
    })
RESULT = tools_list
"""
    try:
        result1 = run_user_code(code1)
        print(f"Result: Found {len(result1.result)} tools")
        for tool in result1.result[:3]:
            print(f"  - {tool['name']} from {tool['module']}")
        print("  ...")
    except RunnerExecutionError as e:
        print(f"Error: {e}")
    print()

    # Example 2: Try to use a Jira tool (will fail if JIRA env vars not set)
    print("Example 2: Get Jira projects (requires JIRA_HOSTNAME and JIRA_PAT)")
    code2 = """
from tools.jira.get_projects import get_projects

try:
    projects = get_projects()
    RESULT = {
        'success': True,
        'count': len(projects),
        'projects': [p['key'] for p in projects[:5]],
    }
except Exception as e:
    RESULT = {
        'success': False,
        'error': str(e),
    }
"""
    try:
        result2 = run_user_code(code2)
        print(f"Result: {result2.result}")
        if result2.logs:
            print(f"Logs: {result2.logs}")
    except RunnerExecutionError as e:
        print(f"Execution Error: {e}")
    print()

    # Example 3: Demonstrate Python control flow
    print("Example 3: Control flow demonstration")
    code3 = """
# Simulate checking multiple issues
mock_issues = [
    {'key': 'PROJ-1', 'status': 'Open'},
    {'key': 'PROJ-2', 'status': 'Closed'},
    {'key': 'PROJ-3', 'status': 'Open'},
]

open_issues = []
for issue in mock_issues:
    if issue['status'] == 'Open':
        open_issues.append(issue['key'])

RESULT = {
    'total': len(mock_issues),
    'open_count': len(open_issues),
    'open_keys': open_issues,
}
"""
    try:
        result3 = run_user_code(code3)
        print(f"Result: {result3.result}")
    except RunnerExecutionError as e:
        print(f"Error: {e}")
    print()

    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
