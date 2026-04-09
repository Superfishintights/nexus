---
name: legacy-toolpack-migration
description: Migrate an older Nexus checkout that still uses legacy `tools/` folders to the newer `tool_packs/` layout while also applying current core/runtime changes with the single-file bundle. Use when updating a pre-tool-pack Nexus repo, preparing another machine for newer Nexus core code, or converting first-party legacy service folders like `tools/jira` into `tool_packs/nexus_tools_jira` packages.
---

# Legacy Toolpack Migration

Update an older Nexus checkout in two stages: apply the current bundled `nexus/` core, then convert the legacy `tools/` service folders into local `tool_packs/` packages that modern Nexus can discover.

## Workflow

1. Confirm the source repo contains the latest `nexus/` core changes and the migration skill files.
2. Build or reuse `nexus_bundle.py` from the source repo.
3. Apply the bundle to the target legacy checkout.
4. Run `scripts/migrate_legacy_tools_to_tool_packs.py` from this skill against the target checkout.
5. Set or update `NEXUS_TOOL_PACKAGES` on the target checkout.
6. Run a lightweight validation pass on the target checkout.

## Bundle Step

Build the current core bundle from the source repo:

```bash
python scripts/build_nexus_bundle.py
```

Apply it to the older checkout:

```bash
python nexus_bundle.py /path/to/legacy-nexus
```

Important:

- The bundle only updates `nexus/` core files and related core metadata.
- It does not include `tool_packs/`.
- It does not convert a legacy `tools/` tree by itself.

## Tool Pack Migration Step

Run the migration script from this skill against the older checkout:

```bash
python skills/legacy-toolpack-migration/scripts/migrate_legacy_tools_to_tool_packs.py \
  --repo-root /path/to/legacy-nexus \
  --update-env
```

What the script does:

- Scans `tools/` for service folders such as `tools/jira`.
- Creates matching packages under `tool_packs/nexus_tools_<service>/`.
- Copies the legacy service files into the new package.
- Rewrites same-service imports from `tools.<service>` to `nexus_tools_<service>`.
- Writes minimal package metadata so Nexus can discover the pack.
- Optionally updates `.env` with the generated `NEXUS_TOOL_PACKAGES` value.

## Safety Checks

Before running the migration script:

- Read `references/assumptions.md`.
- Verify the target repo is a legacy checkout with a real `tools/` tree.
- Verify the target repo does not already have curated first-party packs you intend to preserve unchanged.

Use `--dry-run` first if the target layout is unclear:

```bash
python skills/legacy-toolpack-migration/scripts/migrate_legacy_tools_to_tool_packs.py \
  --repo-root /path/to/legacy-nexus \
  --dry-run
```

## Validation

After migration, validate on the target checkout:

```bash
python -m py_compile $(rg --files /path/to/legacy-nexus/tool_packs -g '*.py')
python /path/to/legacy-nexus/nexus/selftest.py
```

If the checkout is run directly from the repo root, modern Nexus can bootstrap local `tool_packs/<name>` directories from the checkout itself. If the target environment installs packages instead of running from the checkout, install the generated packs explicitly.

## Limits

- This workflow is designed for first-party-style legacy layouts like `tools/<service>/...`.
- It does not infer service-specific env var renames.
- It only rewrites imports that point back into the same service package.
- If legacy modules import `tools.<other_service>` or other shared legacy modules, inspect and patch those manually after generation.

## Resources

- `scripts/migrate_legacy_tools_to_tool_packs.py`: Generates `tool_packs/` packages from a legacy checkout.
- `references/assumptions.md`: Migration assumptions, unsupported layouts, and manual follow-up items.
