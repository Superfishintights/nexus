# nexus_tools_audiobookshelf

Production-oriented Nexus tools for Jay's Audiobookshelf library, reconciled
against Audiobookshelf 2.36.0. The pack exposes a curated 60-tool management
surface; see `docs/endpoint-inventory.md` for included and deferred endpoints.

## Configuration

```dotenv
AUDIOBOOKSHELF_URL=https://abs.example.com
AUDIOBOOKSHELF_API_TOKEN=replace-with-a-user-api-token
AUDIOBOOKSHELF_TIMEOUT_S=30

# Optional curl --resolve-style direct connection. The URL hostname remains the
# HTTP Host and TLS SNI/certificate hostname; TLS verification stays enabled.
AUDIOBOOKSHELF_RESOLVE=abs.example.com:443:192.0.2.10

# Required before any local file upload. Comma-separated absolute roots.
AUDIOBOOKSHELF_UPLOAD_ROOTS=/home/user/Books,/home/user/Downloads
AUDIOBOOKSHELF_MAX_UPLOAD_BYTES=21474836480
```

`AUDIOBOOKSHELF_RESOLVE` never disables certificate verification and must match
the configured URL hostname and port. The IP is used only as the socket target.

Uploads resolve symlinks, require regular files beneath an allowlisted root,
enforce endpoint-specific extensions and a total byte limit, and stream file
content without loading the whole upload into memory.

## Install and enable

```bash
python -m pip install -e tool_packs/nexus_tools_audiobookshelf
```

Add `nexus_tools_audiobookshelf` to `NEXUS_TOOL_PACKAGES`, then restart the
Nexus server so the runtime catalog is rebuilt.

## Validation

```bash
python -m py_compile tool_packs/nexus_tools_audiobookshelf/nexus_tools_audiobookshelf/*.py
pytest -q tool_packs/nexus_tools_audiobookshelf/tests --import-mode=importlib
python ~/.codex/skills/nexus-tool-builder/scripts/validate_nexus_toolset.py \
  --service-dir tool_packs/nexus_tools_audiobookshelf/nexus_tools_audiobookshelf \
  --namespace audiobookshelf --expected-canonical 60 --strict-counts
```

Development and CI must not exercise write, admin mutation, upload, or
destructive tools against a live library. Those paths are covered with mocks.
