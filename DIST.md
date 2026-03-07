# Distribution Guide

This repo includes a single-file Nexus bundle for environments where cloning or
copying many files is impractical.

## Files

- `nexus_bundle.py`: self-extracting bundle containing the current `nexus/` tree
- `scripts/build_nexus_bundle.py`: regenerates `nexus_bundle.py`
- `BUNDLE.md`: short reference for the bundle workflow

## Rebuild The Bundle

From the repo root:

```bash
python scripts/build_nexus_bundle.py
```

That rewrites:

```text
nexus_bundle.py
```

## Use The Bundle On Another Machine

Copy/paste the contents of `nexus_bundle.py` onto the target machine and save it
somewhere accessible.

Apply it to an existing Nexus checkout:

```bash
python nexus_bundle.py /path/to/existing/nexus-repo --dry-run
python nexus_bundle.py /path/to/existing/nexus-repo
```

## What It Does

- creates missing directories under the target repo
- rewrites bundled files under `nexus/`
- backs up changed files before overwriting them

Backups go to:

```text
/path/to/existing/nexus-repo/bundle-backups/<timestamp>/
```

## Useful Flags

- `--list`: print embedded metadata and all bundled file paths
- `--dry-run`: show which files would be updated without writing them
- `--no-backup`: skip changed-file backups
- `--backup-dir <dir>`: choose a different backup directory

## Current Bundle Scope

The generated bundle includes the `nexus/` source tree only:

- Python modules under `nexus/`
- `nexus/pyproject.toml`
- test files under `nexus/`

It does not include:

- `tools/`
- local caches
- `__pycache__`
- build artefacts

## Recommended Work-Laptop Flow

1. Update your local repo here and rebuild `nexus_bundle.py`.
2. Copy/paste `nexus_bundle.py` to the work laptop.
3. Run `--dry-run` against the existing Nexus checkout.
4. Run the real apply command.
5. Optionally run:

```bash
python nexus/selftest.py
```
