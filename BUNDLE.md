# Nexus Bundle

This repo can generate a single-file bundle for copy/paste deployment of `nexus-core` files.

Build:

```bash
python scripts/build_nexus_bundle.py
```

Output:

- `nexus_bundle.py`

Apply on target checkout:

```bash
python nexus_bundle.py /path/to/existing/repo
```

Flags:

- `--dry-run`
- `--list`
- `--no-backup`
- `--backup-dir <dir>`

## Scope

Bundle profile is core-only (`nexus/**`):

- Runtime modules under `nexus/`
- `nexus/pyproject.toml`
- Core tests under `nexus/`

Not included:

- `tool_packs/`
- legacy `tools/`
- caches and build artifacts
