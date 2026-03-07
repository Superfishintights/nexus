# Nexus Bundle

This repo can generate a single-file bundle for copy/paste deployment of the
`nexus/` tree.

Build it:

```bash
python scripts/build_nexus_bundle.py
```

That produces:

- `nexus_bundle.py`

Use it on the target machine:

```bash
python nexus_bundle.py /path/to/existing/repo
```

Helpful flags:

- `--dry-run`: show which files would be rewritten
- `--list`: list embedded files
- `--no-backup`: skip file backups
- `--backup-dir <dir>`: choose where changed-file backups are stored

The current bundle profile includes only `nexus/**` and excludes local cache and
build artefacts.
