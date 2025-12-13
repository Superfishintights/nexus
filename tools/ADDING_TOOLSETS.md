# Adding Toolsets (template + conventions)

This repo is designed for **large** tool libraries without MCP “tool schema bloat”.
The model only talks to Nexus via `search_tools`, `get_tool`, and `run_code`; everything
else is discovered and loaded on demand.

## Recommended layout (per service)

For a new service named `acme`, create:

```text
tools/acme/
  __init__.py
  client.py
  api.py
```

Split `api.py` into multiple files when it grows (Nexus scans subpackages recursively).

### When to keep `api.py` vs split

Start with a single `api.py` for small, cohesive toolsets. Split into multiple modules
when any of these happen:

- You have ~20+ tools for the service.
- `api.py` grows past a few hundred lines or spans multiple resource areas.
- You want finer-grained lazy loading (importing one tool shouldn’t register 100 others).

Trade-offs (important for performance):

- `search_tools` builds the catalog by AST-parsing every `*.py` file in tool packages.
  More files generally means more filesystem + parse work per search.
- `load_tool("...")` imports a single module. Fewer/bigger modules mean more tools are
  loaded/registered per import.

This is separate from MCP “context bloat”: Nexus only returns filtered tool metadata to
the model. Layout decisions are about maintainability and runtime costs.

## Tool naming (avoid collisions)

Tool names must be globally unique across **all** configured tool packages.

For multi-service installs, use `namespace=` on every tool:

- Tool name becomes `"{namespace}.{function_name}"`
- Example: `namespace="jira"` + `def get_issue_status(...)` → `jira.get_issue_status`

This prevents ambiguous names like `get`, `list`, `search`, etc.

## Minimal tool template

```python
from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="acme",
    description="Short, verb-first summary of what this does.",
    examples=[
        'load_tool("acme.get_widget")("W-123")',
    ],
)
def get_widget(widget_id: str) -> Dict[str, Any]:
    """Optional longer docstring with edge cases and return shape."""
    client = get_client()
    return client.get_widget(widget_id)
```

### Important: keep metadata literal for AST scanning

Nexus discovers tools via AST scanning (no imports). To make discovery accurate:

- Tool modules must be valid Python (syntax errors mean the file is skipped).
- Keep `namespace="..."`, `name="..."`, `description="..."`, and `examples=[...]` as **literal strings/lists**.
- Put any computed documentation in the function docstring (which is also scanned).

### Optional: typed settings (`RUNNER_SETTINGS`)

Most tool clients should read configuration directly via `nexus.config.get_setting`
from the environment or `.env`. Per-service settings under `nexus/settings/*` are
optional and exist to expose typed config to code executed via `run_code` (available as
`RUNNER_SETTINGS`).

Only add a `nexus/settings/<service>.py` module if you want:

- validation in one place (required env vars, URL normalization, fallbacks)
- a typed settings object available to snippets (`RUNNER_SETTINGS.<service>`)

If you do add one:

1. Create `nexus/settings/<service>.py` as a dataclass with a `from_env()` classmethod.
2. Wire it into `nexus/settings/runner.py` so it’s loaded into `RunnerSettings`.
3. Export it from `nexus/settings/__init__.py` and `nexus/config.py`.

## Shared client template (standard library HTTP)

Keep network/config handling in one place so tools stay tiny:

```python
from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, Optional

from nexus.config import get_setting


class AcmeClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or get_setting("ACME_URL") or "").rstrip("/")
        self.token = token or get_setting("ACME_TOKEN")
        if not self.base_url or not self.token:
            raise ValueError("Missing ACME_URL or ACME_TOKEN")

    def get_widget(self, widget_id: str) -> Dict[str, Any]:
        req = urllib.request.Request(
            f"{self.base_url}/api/widgets/{widget_id}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))


_default_client: Optional[AcmeClient] = None
_default_client_key: Optional[tuple[str, str]] = None


def get_client() -> AcmeClient:
    global _default_client, _default_client_key
    base_url = get_setting("ACME_URL") or ""
    token = get_setting("ACME_TOKEN") or ""
    key = (base_url, token)
    if _default_client is None or _default_client_key != key:
        _default_client = AcmeClient(base_url=base_url, token=token)
        _default_client_key = key
    return _default_client
```

## Quick checklist

- Pick a stable `namespace` (e.g., `jira`, `gitlab`, `acme`).
- Make tool return values JSON-serializable (dict/list/str/int/bool/None).
- Avoid import-time side effects (no network calls when the module is imported).
- Use `search_tools` and `get_tool` to validate discoverability.
- Validate syntax: `python -m py_compile tools/<service>/*.py`.
- Run `pytest -q` from repo root after changes.
