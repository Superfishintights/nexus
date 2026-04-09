# Nexus MCP Server

Nexus is a code-mode Model Context Protocol (MCP) server. Core runtime and tool packs are now split for distribution:

- `nexus-core`: MCP server/runtime (`nexus/`)
- Tool packs: separate Python packages with distinct import roots

This repo remains a monorepo for development.

## Requirements

- Python `>= 3.10` (see `nexus/pyproject.toml`)

## Install

Install core:

```bash
pip install -e ./nexus
```

Install only the tool packs you want:

```bash
pip install -e ./tool_packs/nexus_tools_jira
pip install -e ./tool_packs/nexus_tools_n8n
```

## Configure Tool Discovery

Nexus no longer assumes a built-in `tools` package by default.
Set `NEXUS_TOOL_PACKAGES` to the installed pack roots:

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_jira,nexus_tools_n8n"
```

When running from this monorepo, Nexus also bootstraps local `tool_packs/<name>`
directories onto `sys.path`, so you can point `NEXUS_TOOL_PACKAGES` at the local
pack roots without separately installing each one.

The legacy value `NEXUS_TOOL_PACKAGES=tools` is treated as a compatibility alias
for all first-party tool packs in the monorepo, but explicit pack names are preferred.

## Run

```bash
python nexus/server.py
```

## Execution model

Nexus keeps a small host/runner boundary:

- `nexus/server.py` is the host-facing MCP surface for `search_tools`,
  `get_tool`, and `run_code`.
- `nexus/runner.py` prepares snippet globals and reuses a pooled persistent execution worker by default.
- `nexus/execution_worker.py` runs snippets in subprocess workers that can serve multiple requests before restart.
- Tool policy and tool loading stay on the Nexus side of the boundary so
  restricted mode can block arbitrary imports while still allowing approved
  canonical tool calls.
- Approved tool calls still consume the snippet's overall execution timeout budget.
- Approved tool calls execute in short-lived subprocesses, so timed-out tool calls
  are killed instead of continuing in detached host threads.
- In pooled mode, waiting for an available worker now counts against the same
  request timeout budget.

Restricted mode is a hardened convenience surface, not a hostile-code sandbox.
It blocks direct imports plus common introspection/frame escapes, but a real
security boundary still requires OS/container isolation.

Set `NEXUS_RUN_CODE_MODE=oneshot` to force the previous spawn-per-call behavior for comparison or debugging.

Persistent-runner tuning knobs:

- `NEXUS_RUN_CODE_MODE=persistent_pool` — default pooled warm workers
- `NEXUS_RUN_CODE_MODE=persistent` — single warm worker, best for sequential latency
- `NEXUS_RUN_CODE_MODE=oneshot` — legacy spawn-per-call mode
- `NEXUS_PERSISTENT_WORKER_POOL_SIZE` — pool size in pooled mode (default `4`)
- `NEXUS_PERSISTENT_WORKER_MAX_REQUESTS` — recycle a worker after N requests (default `100`)
- `NEXUS_PERSISTENT_WORKER_IDLE_SECONDS` — recycle a worker after idle time (default `300`)

## Phase-1 benchmark harness

Generate a machine-readable baseline for the current catalog + runner path:

```bash
python -m nexus.benchmark_phase1 --iterations 5 --warmups 1
```

This writes a JSON report under `.omx/benchmarks/` by default and gives you a repeatable baseline for:

- catalog listing/search latency,
- `get_tool` lookup latency,
- trivial `run_code` latency, and
- lazy `TOOLS.search(...)` orchestration latency.

## Self-test (stdlib only)

```bash
python nexus/selftest.py
python nexus/selftest.py --benchmark
python nexus/selftest.py --compare-run-modes --benchmark-iterations 5 --benchmark-warmups 1
```

## Configuration (cross-platform)

Nexus reads settings from:

1) Process environment variables
2) A `.env` file

Supported `.env` locations (lowest precedence to highest):

- User config:
  - Linux: `~/.config/nexus/.env` (or `$XDG_CONFIG_HOME/nexus/.env`)
  - macOS: `~/Library/Application Support/nexus/.env`
  - Windows: `%APPDATA%\\nexus\\.env`
- Project-local: `./.env`

Override lookup with `NEXUS_ENV_FILE`.

## Tool Pack Import Roots

Current first-party pack roots:

- `nexus_tools_jira`
- `nexus_tools_n8n`
- `nexus_tools_sonarr`
- `nexus_tools_radarr`
- `nexus_tools_tautulli`
- `nexus_tools_starling`

## MCP Client Setup

Nexus is a stdio MCP server. Configure your client to run:

- Command: `python`
- Args: `nexus/server.py`
- Working directory: repo root

```json
{
  "mcpServers": {
    "nexus": {
      "command": "python",
      "args": ["nexus/server.py"],
      "cwd": "/absolute/path/to/nexus-repo"
    }
  }
}
```
