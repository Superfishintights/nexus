# PLAN: Tool Authoring Conventions + n8n Cleanup

This file is a handoff plan for implementing remaining cleanup and consistency work in this repo.
It is written for a fresh context window (assume the reader has not seen prior discussion).

## Background (how Nexus discovers/loads tools)

- Nexus exposes only three MCP tools: `search_tools`, `get_tool`, and `run_code`.
- Tool discovery is **static**: `nexus/tool_catalog.py` walks `*.py` files in configured tool packages and uses `ast.parse` to find top-level functions decorated with `@register_tool`.
- Tool loading is **lazy**: `load_tool("name")` imports one Python module (which registers tools at import time).

Implications:

- **Every tool file must be valid Python**. If a module has a syntax error, it will be skipped by the catalog and its tools will not be discoverable.
- File organization affects runtime costs:
  - More/smaller modules ⇒ slower catalog scan (more files), but more granular lazy imports.
  - Fewer/larger modules ⇒ faster scan, but importing one tool loads/registers more at once.
- Tool names must be globally unique across all configured tool packages.
  - Preferred convention: set `namespace="service"` on every tool so tool names are `service.tool_name` (e.g., `sonarr.get_series`).

## Goals

1. Make tool authoring expectations unambiguous (docs already updated; verify consistency).
2. Fix the built-in `tools/n8n/*` modules so they are:
   - syntactically valid Python
   - discoverable by the AST catalog
   - collision-safe via `namespace="n8n"` (or another consistent naming strategy)
3. Add a small regression test so “n8n is undiscoverable due to syntax errors” can’t silently recur.

## Non-goals

- Do not expand n8n API coverage or change behavior beyond syntax/naming/discoverability.
- Do not add network calls at import time.
- Do not introduce new third-party dependencies.

## Work Items (do these in order)

### 1) Fix `tools/n8n/*` to be Python-parseable

Problem symptoms:

- The n8n files currently contain literal backslashes in docstrings (e.g. `\"\"\"`), which is invalid Python at top-level.
- `tools/n8n/client.py` contains an invalid f-string expression due to escaping inside the `{...}` expression.

Actions:

1. Remove the stray backslashes before quotes in all n8n modules.
   - Example: change `\"\"\"Doc\"\"\"` → `"""Doc"""` and `\"` → `"` where appropriate.
2. Fix the f-string expression in `tools/n8n/client.py`:
   - Current pattern: `f"{... endpoint.lstrip(\"/\") ...}"` (invalid)
   - Fix by using single quotes inside the expression: `endpoint.lstrip('/')`
   - Or avoid quoting inside the f-string expression by moving the call outside.
3. Verify the entire tool tree parses:
   - `python -m py_compile tools/n8n/*.py`

Acceptance criteria:

- `python -m py_compile tools/n8n/*.py` exits with code 0.

### 2) Make n8n tool names unambiguous (choose one convention)

Preferred convention (recommended):

- Add `namespace="n8n"` to every `@register_tool(...)` in `tools/n8n/*.py`.
- Update `examples=[...]` strings to use the namespaced tool names, e.g.:
  - `examples=['load_tool("n8n.create_workflow")(...)]` or `examples=["n8n.create_workflow(...)"]`

Alternative (not preferred, but acceptable if you need backwards compatibility):

- Prefix function names instead (e.g., `n8n_create_workflow`) and keep `namespace=None`.
- This is the pattern used by the built-in Tautulli toolset (e.g. `tautulli_get_activity`).

Implementation notes:

- The catalog extracts decorator metadata only when it’s literal. Keep `namespace="n8n"` and `examples=[...]` as literal strings/lists.
- If you introduce namespacing, update any internal references that call tools by name (examples/docs/tests).

Acceptance criteria:

- `python - <<'PY'\nfrom nexus.tool_catalog import get_catalog\nc = get_catalog(refresh=True)\nprint('n8n.create_workflow' in c)\nPY` prints `True` (or equivalent for whichever n8n tool you choose to assert).

### 3) Add a regression test for built-in n8n discoverability

Goal: prevent future “tools exist on disk but are undiscoverable” regressions.

Suggested test:

- Update `nexus/test_tool_catalog.py` to assert at least one n8n tool is present in the built-in catalog:
  - If using namespacing: assert `"n8n.create_workflow" in catalog` (or another stable tool).
  - If using prefix naming: assert `"n8n_create_workflow" in catalog`.

Why this helps:

- The AST scanner silently skips syntax errors, so without a test, broken tool files can slip in unnoticed.

Acceptance criteria:

- `pytest -q` passes.

### 4) Decide whether `nexus/settings/n8n.py` should exist (optional)

Important: a per-service settings module is **not required** for tools to work.

- Tool clients can read env vars directly via `nexus.config.get_setting` (like `tools/tautulli/client.py` and `tools/sonarr/client.py`).
- `nexus/settings/*` exists to expose a typed, validated settings object to `run_code` snippets via `RUNNER_SETTINGS`.

Only add `nexus/settings/n8n.py` if you want one or more of:

- `RUNNER_SETTINGS.n8n` to exist for executed snippets
- shared validation/normalization logic that multiple tools use

If you choose to add it:

1. Create `nexus/settings/n8n.py` with a dataclass (e.g., `N8nSettings`) and a `from_env()` classmethod.
2. Update `nexus/settings/runner.py`:
   - add `n8n: Optional[N8nSettings] = None`
   - load it inside `from_env()` with `try/except ConfigurationError` (matching other services)
3. Update exports:
   - `nexus/settings/__init__.py`
   - `nexus/config.py`

Acceptance criteria (if implemented):

- `python - <<'PY'\nfrom nexus.runner import build_execution_globals\nns = build_execution_globals()\nprint(hasattr(ns['RUNNER_SETTINGS'], 'n8n'))\nPY` prints `True`

### 5) Final validation

Run:

- `python -m py_compile tools/n8n/*.py`
- `pytest -q`
- Optional sanity check: `python nexus/test_runner.py` and confirm the tool catalog includes the n8n tools you expect.

## Notes for the implementer

- Keep tool modules small and avoid import-time side effects (no network calls at import).
- Prefer `namespace="service"` for multi-service installs; it prevents collisions without forcing prefixed function names.
- If you change tool names (e.g., adding `namespace="n8n"`), treat it like an API change: update examples and any callers.
