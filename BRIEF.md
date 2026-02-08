# Nexus Brief (Context + Constraints)

This repo implements a "code-mode" MCP server: expose a tiny MCP surface (`search_tools`, `get_tool`, `run_code`) and let models orchestrate arbitrarily many domain tools in Python (progressive disclosure + local control-flow).

This document exists so a fresh session can quickly understand why certain design choices and limitations exist, especially for corporate environments.

## What This File Is For

This BRIEF is intended to be the canonical, detailed plan of record for near-term
engineering changes to Nexus.

It should answer:
- What we are changing and why (including corporate constraints).
- Exactly what code needs to change (file-level pointers).
- How to validate the changes (tests, acceptance criteria).

## Operating Reality (Why The Limitations Exist)

Primary target environments:

- **Corporate macOS (Jamf-managed, locked down)**
  - No Homebrew.
  - Cannot install arbitrary packages; anything new requires approval.
  - No separate OS users / containers / daemon-level sandboxing is realistically possible.
  - Python is available, but practical compatibility is constrained:
    - Corporate/internal `fastmcp` works on **Python <= 3.13**.
    - System Python may be newer (e.g. 3.14), but relying on it risks incompatibility.
  - Repo is often deployed by **copy/paste** (cannot `git clone`).

- **Home Linux (full control)**
  - Can use OS-level isolation and tooling.
  - Can experiment with stronger sandboxing approaches safely.

Implications:

- **No new third-party dependencies** should be required for core operation.
- Keep a **copy/paste runnable** path: `python nexus/server.py` from the repo root.
- Prefer changes that improve performance/reliability without reducing capability.
- Any sandboxing must be **optional and profile-driven**, because the corporate Mac
  cannot support “proper” OS isolation without approvals.

## Current Strengths (Keep These)

- Avoids MCP tool-schema bloat by searching the catalog on demand.
- Avoids intermediate-result bloat by doing loops/joins/filters in Python and returning only `RESULT`.
- Tool discovery is static (AST scan) and tool loading is lazy (import-on-demand).
- Namespacing scales across many services (preferred: `service.tool_name`).

## Current Risks (Known / Accepted For Now)

- `run_code` executes arbitrary Python (`exec`) and exposes `__import__`.
  - This enables "unregistered" actions, which is convenient and sometimes desired.
  - It is also a security and stability risk if a model goes off the rails.
  - Corporate Mac cannot realistically run a strict OS sandbox, so mitigation must be pragmatic.

## Near-Term Improvements (No-Dependency, Usability-Preserving)

These are the next changes to implement and validate. They are designed to be safe
for corporate macOS and do not require new packages.

### 1) Incremental Tool Catalog Refresh (Keep "Instant Refresh", Faster)

Problem:
- `get_catalog(refresh=True)` rebuilds the entire catalog, scanning and parsing
  every tool file (AST) on each MCP call path that refreshes.
- This is correct but can become expensive as tool packages grow.

Approach:
- Add a per-file cache keyed by `(path, mtime_ns, size)` (or similar) that stores
  the extracted `ToolSpec` list for that file.
- On refresh:
  - re-scan the filesystem to enumerate candidate files
  - for each file, only re-parse if the fingerprint changed
  - drop cache entries for deleted files
- Preserve current behavior:
  - syntax errors silently skip files
  - duplicate tool-name detection across packages remains a hard error

Files:
- `nexus/tool_catalog.py`

Validation / acceptance:
- No behavior change in tool listings when files are unchanged.
- `pytest -q` passes.
- Add a new targeted test that asserts "refresh" does not re-parse unchanged
  files (instrument by monkeypatching `ast.parse` or `scan_file` and counting).

### 2) Make `TOOLS` Truly Lazy In `run_code`

Problem:
- `nexus/runner.py` currently builds `TOOLS` as an eager dict of every tool
  (even in "summary" form). This defeats some of the "progressive disclosure"
  advantage inside `run_code`, and adds overhead to every execution.

Approach:
- Replace the eager `TOOLS` dict with a small Mapping-like wrapper:
  - supports `__contains__`, `__iter__`, `items()`, `keys()`, `values()`, and `get()`
  - fetches from the catalog on demand (and caches within the wrapper instance)
- Add convenience methods for common model workflows:
  - `TOOLS.search(query: str, limit: int = 20, detail_level: str = "summary")`
  - `TOOLS.get_tool(name: str, detail_level: str = "full")`
- Keep compatibility with existing snippets:
  - `name in TOOLS`
  - `TOOLS["jira.get_issue_status"]` or `TOOLS.get(name)`
  - iteration / `.items()` should still work, but may be more expensive by design

Files:
- `nexus/runner.py`
- potentially a new helper module, e.g. `nexus/lazy_tools.py` (stdlib only)

Validation / acceptance:
- `pytest -q` passes.
- Add a new runner test that asserts `build_execution_globals()` does not
  eagerly call `get_catalog(refresh=True)` more than necessary, and that
  `TOOLS.search(...)` returns results consistent with `search_catalog(...)`.

### 3) Standardize Tool Naming Without Breaking Existing Calls

Problem:
- Namespacing (`service.tool`) is the scalable convention, but older tools or
  examples may still use un-namespaced names.
- Renaming tools is an API change for model prompts and stored automations.

Approach:
- Make namespaced names canonical everywhere:
  - new tools should always set `namespace="service"`
  - docs/examples should use namespaced tool names
- Preserve compatibility:
  - support registering aliases so the old un-namespaced names continue to load
  - ensure `search_tools` prefers canonical names in output, but optionally
    includes alias metadata (so models can migrate)

Implementation sketch (no new deps):
- Extend `register_tool` and/or registry to support aliases:
  - `@register_tool(namespace="jira", aliases=["get_issue_status"])` (proposed)
  - or a separate `register_alias("get_issue_status", "jira.get_issue_status")`
- Ensure `ensure_tool_loaded(name)` resolves aliases correctly.

Files:
- `nexus/tool_registry.py`
- `nexus/tool_catalog.py` (catalog should ideally know aliases, or aliases should
  be resolved after load; decide and document)
- `tools/*` (update decorators/examples to use namespaces where missing)

Validation / acceptance:
- Back-compat: existing un-namespaced names still work.
- Canonical: namespaced names are discoverable and loadable.
- Add tests asserting both names resolve to the same callable.

### 4) Reduce Response Size / Token Overhead From MCP Endpoints

Problem:
- MCP endpoints currently pretty-print JSON responses which increases tokens and
  IO size without functional benefit.

Approach:
- Stop indenting JSON responses; keep stable key names.
- Keep `ensure_ascii=False` for readability with non-ASCII text.

Files:
- `nexus/server.py`

Validation / acceptance:
- `pytest -q` passes.
- Output remains valid JSON and schema-compatible (just smaller).

### 5) Client Robustness Improvements (No Behavior Change Intended)

Problem:
- HTTP client calls without timeouts can hang requests and effectively hang the
  model workflow.
- Some query-param handling needs to be correct and consistent.

Approach:
- Add explicit timeouts to built-in service clients (Jira, n8n).
- Ensure n8n query params are URL-encoded correctly.

Files:
- `tools/jira/client.py`
- `tools/n8n/client.py`

Validation / acceptance:
- Unit tests should not require network access; add tests around URL construction
  and parameter encoding.
- Ensure no network calls happen at import time.

### 6) Add A Stdlib Self-Test (No pytest Dependency)

Problem:
- Copy/paste deployments may not have pytest installed; we still want a quick
  health check.

Approach:
- Add `nexus/selftest.py` executable script that:
  - compiles core modules and tool modules (`py_compile`)
  - builds the catalog
  - asserts a handful of expected tool names (and aliases if introduced)
  - runs a minimal `run_code` snippet that sets `RESULT`

Files:
- new `nexus/selftest.py`

Validation / acceptance:
- `python nexus/selftest.py` exits 0 in a clean environment with only runtime deps.

## Validation Checklist (When Implementing The Above)

- `python -m py_compile $(find nexus tools -name '*.py')`
- `python -m pytest -q` (when pytest is available)
- Start server: `python nexus/server.py`
- `search_tools` returns expected tools and does not regress naming conventions
- `run_code` can `load_tool(...)` and set `RESULT`

## Local Testing Env

Use a project-local `.env` at repo root (preferred). This repo includes:
- `./.env.example` (template, tracked)
- `./.env` (local, gitignored)

Fill in `./.env` to test built-in tools:
- `JIRA_HOSTNAME`, `JIRA_PAT`
- `N8N_HOST`, `N8N_API_KEY`
- `SONARR_URL`, `SONARR_API_KEY`
- `TAUTULLI_URL`, `TAUTULLI_API_KEY`

`NEXUS_TOOL_PACKAGES` can be set to include additional tool packages.

## Sandboxing Direction (Goal: Zero Intended Functionality Loss)

We want a future sandbox that:

- prevents "nuke the world" failure modes (infinite loops, runaway output, accidental filesystem damage),
- *while still allowing intended integrations* (Jira/etc over the network, including environments with SSL friction),
- and remains viable on locked-down macOS.

Likely approach (phased, profile-based):

- Phase A (works everywhere): **stability isolation**
  - Execute snippets in a subprocess with timeouts and output limits.
  - No capability restrictions; just prevents hangs from taking down the server.

- Phase B (where possible, Linux/home): **OS-level isolation**
  - Use stronger sandboxing on Linux (namespaces, restricted FS mounts, etc.).
  - Keep network egress allowed, but restrict filesystem to known roots.

- Phase C (optional policy, only if needed): **soft restrictions**
  - Optional import filtering / filesystem allowlists.
  - Must be an explicit “profile”, not the default, to avoid harming usability at work.

Non-goals:

- No "warnings" UX added to the normal workflow.
- No packaging change that breaks copy/paste deployment.
