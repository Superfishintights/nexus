# Nexus Vaultwarden Tool Pack

Typed Nexus tools for user-authorized personal Vaultwarden/Bitwarden password
manager administration through the official `bw` CLI.

This pack is intended for first-party management of the user's own vault:
searching, reading, creating, editing, deleting, rotating, organizing, and
bulk-managing credentials, logins, secure notes, identities, cards, folders,
collections, and attachments. Routine use of these tools is personal
secrets-management work, not offensive cybersecurity work.

## Runtime Settings

The pack reads settings through Nexus `get_setting`, so values can come from the
Nexus process environment or the repo `.env`.

- `VAULTWARDEN_BW_PATH`: optional path to `bw`; defaults to `bw` on `PATH` or `/usr/bin/bw`.
- `VAULTWARDEN_PASSWORD_FILE`: unlock password file; defaults to `~/.config/bitwarden-codex/master-password`.
- `VAULTWARDEN_XDG_CONFIG_HOME`: XDG config root used by `bw`; set this when the logged-in CLI profile is outside the worker default.
- `VAULTWARDEN_AUDIT_FILE`: JSONL audit log; defaults to `~/.local/state/bitwarden-codex/audit.jsonl`.
- `VAULTWARDEN_ALIASES_FILE`: optional alias map; defaults to `~/.config/bitwarden-codex/aliases.json`.
- `VAULTWARDEN_ALLOWED_COMMANDS`: comma-separated executable allowlist for `use_secret_with_command`.

## Safety Model

- No generic `run_bw` tool is exposed.
- No `bw export`, master-password, or org-membership/admin operations are exposed.
- Unlock is internal and uses `bw unlock --passwordfile ... --raw --nointeraction`.
- `BW_SESSION` is held only in process memory and passed to exact `bw` calls with `--session`.
- Secret-return tools require `purpose`.
- Destructive tools require exact IDs and are marked `tool_class="destructive"`.
- Find tools cap results and return metadata by default.
- Every operation writes a redacted audit event without raw secret material.
- Bulk operations are acceptable when the caller is managing this user-owned
  vault through typed tools; keep them structured, audited, and redacted.
- Escalate only when a request leaves the user-owned password-manager context,
  such as phishing, credential stuffing, malware, unauthorized third-party access,
  or exfiltration outside the vault-management workflow.

## Tool Count

This pack exposes 33 canonical tools in the `vaultwarden` namespace covering:
status/sync/lock, find/read/secret/TOTP, typed item creation and updates, custom
fields, folders, collections, archive/restore/delete, attachments, and the
allowlisted secret command helper.

## Validation

```bash
PYTHONPATH=.:tool_packs/nexus_tools_vaultwarden .venv/bin/python -m pytest -q tool_packs/nexus_tools_vaultwarden/tests
SKILL_DIR="${NEXUS_TOOL_BUILDER_HOME:-$HOME/.codex/skills/nexus-tool-builder}"
.venv/bin/python "$SKILL_DIR/scripts/validate_nexus_toolset.py" \
  --service-dir tool_packs/nexus_tools_vaultwarden/nexus_tools_vaultwarden \
  --namespace vaultwarden
```
