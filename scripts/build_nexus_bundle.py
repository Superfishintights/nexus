#!/usr/bin/env python3
"""Build a single-file Nexus bundle for copy/paste deployments.

The generated output is a self-extracting Python script. It embeds selected
repo files as compressed JSON and can rewrite them into an existing checkout.
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import gzip
import hashlib
import json
import time
from pathlib import Path
from string import Template


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "nexus_bundle.py"
INCLUDE_SUFFIXES = {".py", ".toml"}
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "jira_nexus.egg-info"}


BUNDLE_TEMPLATE = Template(
    """#!/usr/bin/env python3
\"\"\"Self-extracting Nexus bundle.

Generated from commit: $commit
Bundle profile: $profile
File count: $file_count
\"\"\"

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


BUNDLE_METADATA = {
    "commit": "$commit",
    "profile": "$profile",
    "generatedAt": "$generated_at",
    "fileCount": $file_count,
}

ARCHIVE_B64 = \"\"\"$archive_b64\"\"\"


def _load_files():
    payload = gzip.decompress(base64.b64decode(ARCHIVE_B64.encode("ascii")))
    return json.loads(payload.decode("utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _backup_file(root: Path, rel_path: str, backup_dir: Path) -> None:
    src = root / rel_path
    if not src.exists():
        return
    dest = backup_dir / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the bundled Nexus files.")
    parser.add_argument(
        "target_root",
        nargs="?",
        default=".",
        help="Repo root to write into. Defaults to current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List bundled files and exit.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not back up changed files before overwriting them.",
    )
    parser.add_argument(
        "--backup-dir",
        default="bundle-backups",
        help="Backup directory root, relative to target_root unless absolute.",
    )
    args = parser.parse_args()

    files = _load_files()

    if args.list:
        print(json.dumps(BUNDLE_METADATA, indent=2))
        for item in files:
            print(item["path"])
        return 0

    target_root = Path(args.target_root).expanduser().resolve()
    backup_root = Path(args.backup_dir).expanduser()
    if not backup_root.is_absolute():
        backup_root = target_root / backup_root
    backup_dir = backup_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    changed = []
    for item in files:
        rel_path = item["path"]
        content = base64.b64decode(item["content_b64"].encode("ascii"))
        digest = _sha256_bytes(content)
        if digest != item["sha256"]:
            raise RuntimeError(f"Integrity check failed for {rel_path}")

        dest = target_root / rel_path
        existing = dest.read_bytes() if dest.exists() else None
        if existing != content:
            changed.append((rel_path, dest, content))

    print(f"Bundle metadata: {json.dumps(BUNDLE_METADATA)}")
    print(f"Target root: {target_root}")
    print(f"Files in bundle: {len(files)}")
    print(f"Files to update: {len(changed)}")

    if args.dry_run:
        for rel_path, _, _ in changed:
            print(f"DRY RUN: would write {rel_path}")
        return 0

    if changed and not args.no_backup:
        print(f"Creating backup at: {backup_dir}")
        for rel_path, _, _ in changed:
            _backup_file(target_root, rel_path, backup_dir)

    for rel_path, dest, content in changed:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        print(f"Wrote {rel_path}")

    if not changed:
        print("No file changes were needed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
)


def _git_commit(root: Path) -> str:
    head = root / ".git" / "HEAD"
    if not head.exists():
        return "unknown"
    ref = head.read_text(encoding="utf-8").strip()
    if ref.startswith("ref: "):
        ref_path = root / ".git" / ref[5:]
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip()
    return ref


def collect_files(root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(root).as_posix()
        normalized = rel_path.replace("\\", "/")
        if not fnmatch.fnmatch(normalized, "nexus/**"):
            continue
        if any(part in EXCLUDED_PARTS for part in file_path.relative_to(root).parts):
            continue
        if file_path.suffix not in INCLUDE_SUFFIXES:
            continue
        content = file_path.read_bytes()
        items.append(
            {
                "path": rel_path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "content_b64": base64.b64encode(content).decode("ascii"),
            }
        )
    return items


def build_bundle(output_path: Path, profile: str) -> None:
    files = collect_files(REPO_ROOT)
    archive_payload = json.dumps(files, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    archive_b64 = base64.b64encode(gzip.compress(archive_payload, compresslevel=9)).decode("ascii")
    rendered = BUNDLE_TEMPLATE.substitute(
        commit=_git_commit(REPO_ROOT),
        profile=profile,
        generated_at=time.time_ns(),
        file_count=len(files),
        archive_b64=archive_b64,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a self-extracting Nexus bundle.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--profile",
        default="nexus-only",
        help="Label embedded into the generated bundle metadata.",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()
    build_bundle(output_path, profile=args.profile)
    print(f"Wrote bundle to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
