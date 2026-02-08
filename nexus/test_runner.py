#!/usr/bin/env python3
"""
Example script demonstrating direct usage of the nexus runner.
This bypasses the MCP server and directly calls run_user_code.
"""

import sys
from pathlib import Path

# Allow running this script from a source checkout without installation.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from nexus.runner import run_user_code, RunnerExecutionError
from nexus.tool_catalog import get_catalog

def main():
    print("=== Nexus Runner Test ===\n")

    # List available tools from the lazy catalog (no imports).
    catalog = get_catalog(refresh=True)
    print("Available tools (catalog):")
    for spec in list(catalog.values())[:10]:
        print(f"  - {spec.name} ({spec.module}) {spec.signature}")
    if len(catalog) > 10:
        print("  ...")
    print()

    # Example 1: List available tools from within executed code
    print("Example 1: Discover tools from code")
    code1 = """
tools_list = []
for name, tool_info in TOOLS.items():
    tools_list.append({
        'name': name,
        'module': tool_info['module'],
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
    print("Example 2: Get Jira issue status (requires JIRA_HOSTNAME and JIRA_PAT)")
    code2 = """
issue_status = load_tool('jira.get_issue_status')

try:
    status = issue_status('PROJ-123')
    RESULT = {
        'success': True,
        'status': status.get('currentStatus', {}).get('name'),
        'transitions': [t['name'] for t in status.get('availableTransitions', [])[:5]],
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
