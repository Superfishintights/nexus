# Migration Assumptions

## Supported legacy layout

The migration script assumes the target checkout uses a service-oriented tree under `tools/`:

```text
tools/
  jira/
    __init__.py
    client.py
    get_issue_status.py
  sonarr/
    ...
```

Each immediate subdirectory of `tools/` is treated as one service and becomes one pack:

- `tools/jira` -> `tool_packs/nexus_tools_jira`
- `tools/sonarr` -> `tool_packs/nexus_tools_sonarr`

## What gets rewritten automatically

Inside copied Python files, the script rewrites imports that stay within the same service:

- `from tools.jira.client import JiraClient` -> `from nexus_tools_jira.client import JiraClient`
- `import tools.jira.client` -> `import nexus_tools_jira.client`

Relative imports like `from .client import get_client` are left unchanged.

## What requires manual review

- Cross-service imports such as `from tools.shared import ...`
- Flat files directly under `tools/` that are not inside a service folder
- Non-standard packaging metadata requirements
- Service configs that changed names after the tool-pack split
- Any generated `README.md` or `pyproject.toml` values you want to customize

## Recommended deployment order

1. Apply the latest core bundle to the target checkout.
2. Run the migration script with `--dry-run`.
3. Run the migration script for real.
4. Inspect any warnings about unresolved `tools.` imports.
5. Run `py_compile` and `nexus/selftest.py` on the target checkout.

## Why the bundle alone is not enough

The bundle builder in this repo only packages `nexus/**` core files. It does not include `tool_packs/`, and it does not transform a legacy `tools/` tree into installable/discoverable packs.
