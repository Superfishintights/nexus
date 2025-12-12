# Nexus MCP Server

Nexus is a “code‑mode” Model Context Protocol (MCP) server. It exposes a small
MCP surface (`run_code`, `search_tools`, `get_tool`) while letting models
orchestrate many domain tools programmatically in Python.

## Install

```bash
pip install -e ./nexus
```

## Run

```bash
python nexus/server.py
```

## Tool Packages

Nexus discovers tools by scanning Python packages for functions decorated with
`@register_tool`. By default it scans the built‑in `tools` package.

To add external tool packages, install them on the machine and set:

```bash
export NEXUS_TOOL_PACKAGES="tools,company_tools,generated_tools"
```

Tools are loaded lazily: use `search_tools` to find what you need, and import or
`load_tool("tool_name")` inside `run_code`.
