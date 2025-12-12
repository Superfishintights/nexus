# Nexus “Code‑Mode MCP” — Idiot’s Guide / Interview Notes

This is a reference sheet for explaining the project in an interview. It covers:

- What Nexus is solving and why MCP needs help at scale.
- How Nexus works end‑to‑end.
- What each file is responsible for.
- How lazy tool discovery/loading works.
- How to write/add tools.
- Limitations and tradeoffs (especially around safety without containers).

If you can walk someone through this document, you understand the system.

---

## 0. The Problem Nexus Solves (High Level)

MCP is great for connecting models to many tools, but it brings two scaling issues:

1. **Tool definition bloat**
   - Typical MCP clients load *all* tool schemas into the model’s context.
   - With dozens of servers and hundreds/thousands of tools, that can cost tens or hundreds of thousands of tokens before the model even starts reasoning.
2. **Intermediate result bloat**
   - If the model calls tools directly, every intermediate result flows *through* the model, consuming context and increasing latency.

Anthropic’s guidance (from their engineering posts) is:

- **Progressive disclosure**: discover tools on demand, not all at once.
- **Programmatic tool calling**: have the model write code that calls tools, so loops/filters/joins happen in code and only final results return to the model.
- **Tool use examples**: give models usage patterns beyond JSON schema.

Nexus implements those ideas in a small Python MCP server.

---

## 1. What Nexus Is

Nexus is an MCP server that exposes only three tools:

- `run_code(code: str)` — execute model‑authored Python to call any domain tool.
- `search_tools(query="", detail_level="summary", limit=20)` — find relevant tools *without loading everything*.
- `get_tool(name, detail_level="full")` — fetch detailed metadata for one tool.

Instead of giving the model 1,000 tool schemas, we give it:

- a **search endpoint** to discover what it needs,
- a **code execution endpoint** to orchestrate those tools.

This is often called “Code Mode”.

---

## 2. Repository Layout

### `nexus/` (the server + runtime)

- `nexus/server.py`
  - FastMCP server entrypoint.
  - Registers MCP tools: `run_code`, `search_tools`, `get_tool`.
  - Converts catalog/registry objects into JSON for the model.

- `nexus/runner.py`
  - Executes Python via `exec`.
  - Builds a controlled global namespace containing:
    - safe-ish builtins
    - `RESULT` placeholder
    - `TOOLS` (lazy catalog summaries)
    - `load_tool(name)` helper
    - optional env config in `RUNNER_SETTINGS`

- `nexus/tool_catalog.py`
  - AST‑based scanner.
  - Finds `@register_tool` functions on disk *without importing modules*.
  - Builds a cached `{name -> ToolSpec}` catalog.
  - Provides `search_catalog(...)` and detail formatting.

- `nexus/tool_registry.py`
  - Runtime registry for tools that are actually imported.
  - `@register_tool` decorator stores `ToolInfo` with:
    - name, module, description
    - signature (from `inspect.signature`)
    - examples (manual hints)
    - the actual callable
  - `ensure_tool_loaded(name)` imports a tool’s module on demand.

- `nexus/config.py`
  - Optional env‑backed settings for services (Jira, Sourcegraph, etc.).
  - Exposed inside code execution as `RUNNER_SETTINGS`.

- `nexus/test_tool_catalog.py`
  - Pytest regression tests proving:
    - catalog scans without import
    - lazy load works
    - runner supports `load_tool`

- `nexus/test_runner.py`
  - Demo script for running the runner without MCP.
  - Useful in interviews to show the flow locally.

### `tools/` (built‑in example tools)

- `tools/jira/client.py`
  - Standard‑library Jira HTTP client.
  - READ/WRITE capable if you add POST/PUT/DELETE helpers.

- `tools/jira/get_issue_status.py`
  - Example `@register_tool` function.
  - Shows how domain tools are structured.

- `tools/__init__.py`, `tools/jira/__init__.py`
  - Package markers.

- `tools/README.md`
  - How to write tools and add external tool packages.

---

## 3. End‑to‑End Flow

### Diagram

```mermaid
flowchart LR
    U[User request] --> M[Model]
    M -->|search_tools| S[Nexus MCP Server]
    S -->|AST catalog search| C[tool_catalog]
    C --> S
    M -->|get_tool| S
    S -->|catalog/registry detail| M
    M -->|run_code| S
    S --> R[runner.exec]
    R -->|load_tool(name)| TR[tool_registry]
    TR -->|import module| TP[tools/* or external pkgs]
    TP --> TR
    R --> S
    S --> M
```

### Step‑by‑step

1. **Model discovers tools**
   - Calls `search_tools("jira status")`.
   - Server uses catalog search to return e.g. `get_issue_status`.

2. **Model fetches details**
   - Calls `get_tool("get_issue_status")`.
   - Server returns full docstring/signature/examples.

3. **Model writes orchestration code**
   - Calls `run_code` with Python that:
     - imports the tool OR calls `load_tool("get_issue_status")`
     - does any loops/filtering/joining in Python
     - assigns `RESULT`.

4. **Runner executes once**
   - Intermediate tool results stay inside Python.
   - Only `RESULT` (and stdout logs) come back to the model.

This is why context usage is low.

---

## 4. Tool Discovery: “Progressive Disclosure”

The key trick is: **scan tools without importing them**.

### Where it happens

In `nexus/tool_catalog.py`:

- `get_tool_package_names()`
  - reads `NEXUS_TOOL_PACKAGES` (comma‑separated).
  - defaults to `tools`.

- `build_catalog()`
  - locates packages via `importlib.util.find_spec`.
  - walks `.py` files.
  - parses them using `ast.parse`.
  - finds functions decorated with `@register_tool`.

- For each tool it extracts:
  - name (`@register_tool(name=...)` or function name)
  - description (`description=...` or docstring)
  - examples (`examples=[...]` if provided)
  - signature (derived from AST)

No imports happen here, so we avoid loading dependencies or executing module code.

### Why this matters

If you had 1,000 tools, importing them all at startup would:

- cost time
- potentially break if some tools require env vars or optional deps
- create big MCP tool lists again

Instead the model sees only search results.

---

## 5. Tool Loading: “Lazy Imports”

Discovery gives metadata only. **Actual callables load only when needed**.

### Where it happens

In `nexus/tool_registry.py`:

```python
def ensure_tool_loaded(name: str) -> ToolInfo:
    if name in _REGISTRY:
        return _REGISTRY[name]

    from .tool_catalog import get_catalog
    spec = get_catalog().get(name)
    importlib.import_module(spec.module)  # triggers @register_tool
    return _REGISTRY[name]
```

### Trigger points

Two ways tools get loaded:

1. **User code imports a module**
   ```python
   from tools.jira.get_issue_status import get_issue_status
   RESULT = get_issue_status("PROJ-123")
   ```
   Import triggers decorator registration.

2. **User code calls `load_tool`**
   ```python
   issue_status = load_tool("get_issue_status")
   RESULT = issue_status("PROJ-123")
   ```
   `load_tool` uses `ensure_tool_loaded`.

Either way, only used tools are imported.

---

## 6. Programmatic Tool Calling via `run_code`

### The MCP tool

In `nexus/server.py`:

```python
@mcp.tool()
def run_code(code: str) -> str:
    result = run_user_code(code)
    return json.dumps({"success": True, "result": result.result, "logs": result.logs})
```

### The execution environment

In `nexus/runner.py`, the model gets:

- `RESULT` placeholder
- `TOOLS` lazy summaries
- `load_tool(name)` helper
- safe builtins

Minimal example:

```python
issue_status = load_tool("get_issue_status")
status = issue_status("PROJ-123")
RESULT = status["currentStatus"]["name"]
```

Complex orchestration (loops/filters) happens in Python *before* returning.

---

## 7. Tool Metadata: Signatures + Examples

Models often fail because schemas alone don’t show real usage.

### Signatures

When a tool is registered (`@register_tool`) we store:

```python
signature = str(inspect.signature(target))
```

This is returned by `get_tool(...)`, so the model knows required/optional params.

### Examples

Tool authors can add:

```python
@register_tool(
    description="Get Jira issue status",
    examples=["get_issue_status('PROJ-123')"],
)
def get_issue_status(issue_key: str) -> dict: ...
```

These examples are gold for interview discussion:

- “schemas define validity, examples teach correctness.”

---

## 8. Adding Tools (First‑party or External)

### First‑party (inside this repo)

1. Add a file under a domain package, e.g. `tools/sourcegraph/search.py`.
2. Decorate a top‑level function with `@register_tool`.
3. That’s it — catalog will find it on next search.

### External packages (work setup)

1. Put tools in a separate installable package, e.g. `company_tools`.
2. Ensure functions use `@register_tool`.
3. Install on the host:
   ```bash
   pip install company-tools
   ```
4. Point Nexus at it:
   ```bash
   export NEXUS_TOOL_PACKAGES="tools,company_tools"
   ```

Nexus will scan both packages lazily.

---

## 9. Safety / Tradeoffs Without Containers

At work you said containers are hard. So:

- **This is not a security boundary.**
  - `exec` + `__import__` means code can import `os`, touch files, etc.
  - If someone malicious controls inputs, they can do damage.

How to explain in interview:

- “We are optimizing *context efficiency and tool correctness*, not hard security.”
- “In a strict environment, you’d wrap this in an OS sandbox; at work we rely on trust + environment controls.”

Even without containers, two practical guardrails you can mention:

- run Nexus as a low‑privilege user
- add timeouts/resource limits if needed (future work)

---

## 10. Talking Points for Interviews

### Why Code Mode?
- Reduces tool definition tokens (progressive disclosure).
- Reduces intermediate token bloat (filtering in code).
- Lets model use native programming constructs for orchestration.

### Why AST scanning?
- Avoids importing every tool at startup.
- Doesn’t require tool dependencies or env vars to be present to be discoverable.

### How lazy loading works?
- Search returns `ToolSpec` (metadata only).
- `ensure_tool_loaded` imports just that module when called.

### What’s next / improvements?
- optional persistent sessions (skills)
- richer search (embeddings) if needed
- resource limits / sandboxing if environment allows

---

## 11. Quick Demo Script

Run:

```bash
python nexus/test_runner.py
```

What it shows:

1. Catalog listing without importing tools.
2. Tool discovery from inside executed code.
3. Lazy loading via `load_tool` and a real Jira call (if env vars set).

---

If it works at work tomorrow, you absolutely should pat yourself on the back.

