# Audiobookshelf pack validation report

Validated on 2026-08-09 against the live Audiobookshelf 2.36.0 server using
read-only calls only. Write, upload, admin-mutation, and destructive paths were
exercised exclusively with mocks and local fixtures.

## Surface

- 60 canonical tools and no aliases
- 19 read, 11 write, 21 admin, 9 destructive
- 59 direct Audiobookshelf routes plus one read-only derived duplicate finder
- 146 direct v2.36.0 routes deliberately deferred; see `endpoint-inventory.md`

## Validation matrix

| Check | Result |
|---|---|
| `git diff --check` | Pass |
| Python compile of every pack module | Pass |
| Pack tests | 230 passed |
| Nexus tool-builder strict validator | 60 canonical, 0 aliases, 0 duplicates, 0 issues |
| Nexus selftest with the pack enabled | Pass |
| Full repository tests with the pack on `PYTHONPATH` | 309 passed |
| Independent read-only production review and focused recheck | No residual actionable findings |
| Local Nexus catalog build/search | 60 tools; `audiobookshelf.search_library` discoverable |
| Live read-only Audiobookshelf smoke | Version 2.36.0; authenticated; one library; minified and expanded item reads valid |

## Commands

```bash
python -m py_compile \
  tool_packs/nexus_tools_audiobookshelf/nexus_tools_audiobookshelf/*.py

pytest -q tool_packs/nexus_tools_audiobookshelf/tests --import-mode=importlib

python ~/.codex/skills/nexus-tool-builder/scripts/validate_nexus_toolset.py \
  --service-dir tool_packs/nexus_tools_audiobookshelf/nexus_tools_audiobookshelf \
  --namespace audiobookshelf \
  --expected-canonical 60 \
  --strict-counts

NEXUS_TOOL_PACKAGES=nexus_tools_audiobookshelf \
PYTHONPATH=tool_packs/nexus_tools_audiobookshelf:. \
python nexus/selftest.py

PYTHONPATH=tool_packs/nexus_tools_audiobookshelf:. \
pytest -q --import-mode=importlib
```

The live smoke used the ignored Nexus `.env` and its TLS-safe
`AUDIOBOOKSHELF_RESOLVE` setting. It called only catalog/search and read-only
Audiobookshelf operations; it did not call maintenance scans, matching,
metadata writes, uploads, user/library/notification writes, backup creation or
restore, progress writes, or deletion.
