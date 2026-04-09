#!/usr/bin/env python3
"""Create local tool_packs packages from a legacy tools/ tree."""

from __future__ import annotations

import argparse
import py_compile
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

SKIP_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache"}
SERVICE_IMPORT_RE = re.compile(r"\btools\.([a-zA-Z0-9_]+)")


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    source_dir: Path
    pack_root: Path
    package_dir: Path

    @property
    def package_name(self) -> str:
        return f"nexus_tools_{self.name}"

    @property
    def distribution_name(self) -> str:
        return f"nexus-tools-{self.name}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy tools/<service> folders into tool_packs packages."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Target legacy Nexus checkout to migrate.",
    )
    parser.add_argument(
        "--services",
        default="",
        help="Comma-separated service names to migrate. Default: all service folders under tools/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing generated pack directories when they already exist.",
    )
    parser.add_argument(
        "--update-env",
        action="store_true",
        help="Upsert NEXUS_TOOL_PACKAGES in the target .env file.",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Specific env file to update. Defaults to <repo-root>/.env when --update-env is set.",
    )
    return parser.parse_args()


def discover_services(repo_root: Path, requested: Sequence[str]) -> List[ServiceSpec]:
    tools_root = repo_root / "tools"
    tool_packs_root = repo_root / "tool_packs"
    if not tools_root.is_dir():
        raise SystemExit(f"Legacy tools directory not found: {tools_root}")

    requested_set = {item.strip() for item in requested if item.strip()}
    services: List[ServiceSpec] = []
    for entry in sorted(tools_root.iterdir()):
        if entry.name in SKIP_NAMES or entry.name.startswith("."):
            continue
        if not entry.is_dir():
            continue
        if requested_set and entry.name not in requested_set:
            continue
        if not any(path.is_file() for path in entry.rglob("*.py")):
            continue
        package_name = f"nexus_tools_{entry.name}"
        pack_root = tool_packs_root / package_name
        services.append(
            ServiceSpec(
                name=entry.name,
                source_dir=entry,
                pack_root=pack_root,
                package_dir=pack_root / package_name,
            )
        )

    if requested_set:
        found = {service.name for service in services}
        missing = sorted(requested_set - found)
        if missing:
            raise SystemExit(f"Requested services not found under tools/: {', '.join(missing)}")

    if not services:
        raise SystemExit("No migratable service folders were found under tools/.")

    return services


def iter_source_files(source_dir: Path) -> Iterable[Path]:
    for path in sorted(source_dir.rglob("*")):
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        if path.is_file():
            yield path


def rewrite_python_imports(text: str, service_name: str, package_name: str) -> tuple[str, List[str]]:
    warnings: List[str] = []

    def replace(match: re.Match[str]) -> str:
        imported_service = match.group(1)
        if imported_service == service_name:
            return package_name
        warnings.append(imported_service)
        return match.group(0)

    rewritten = SERVICE_IMPORT_RE.sub(replace, text)
    return rewritten, sorted(set(warnings))


def write_text(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_service(service: ServiceSpec, *, dry_run: bool, force: bool) -> List[str]:
    if service.pack_root.exists():
        if not force:
            raise SystemExit(
                f"Pack directory already exists: {service.pack_root} (use --force to replace it)"
            )
        if not dry_run:
            shutil.rmtree(service.pack_root)

    warnings: List[str] = []
    package_init = f'"""Migrated {service.name} tools for Nexus."""\n'
    pyproject = (
        "[build-system]\n"
        'requires = ["setuptools>=45", "wheel"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        "[project]\n"
        f'name = "{service.distribution_name}"\n'
        'version = "0.1.0"\n'
        f'description = "Nexus tool pack: {service.name}"\n'
        'readme = "README.md"\n'
        'requires-python = ">=3.10"\n'
        'dependencies = [\n'
        '    "nexus-core>=0.1.0",\n'
        ']\n\n'
        '[tool.setuptools.packages.find]\n'
        'where = ["."]\n'
        f'include = ["{service.package_name}*"]\n'
    )
    readme = (
        f"# {service.package_name}\n\n"
        f"Migrated from `tools/{service.name}` in a legacy Nexus checkout.\n"
    )

    write_text(service.pack_root / "pyproject.toml", pyproject, dry_run)
    write_text(service.pack_root / "README.md", readme, dry_run)
    write_text(service.package_dir / "__init__.py", package_init, dry_run)

    for source_file in iter_source_files(service.source_dir):
        relative = source_file.relative_to(service.source_dir)
        destination = service.package_dir / relative
        if source_file.suffix == ".py":
            original = source_file.read_text(encoding="utf-8")
            rewritten, file_warnings = rewrite_python_imports(
                original,
                service.name,
                service.package_name,
            )
            warnings.extend(
                f"{source_file}: unresolved legacy import to tools.{name}" for name in file_warnings
            )
            write_text(destination, rewritten, dry_run)
            continue

        if dry_run:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)

    return warnings


def update_env_file(env_file: Path, package_names: Sequence[str], dry_run: bool) -> None:
    value = ",".join(package_names)
    new_line = f"NEXUS_TOOL_PACKAGES={value}"
    lines: List[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()

    replaced = False
    result: List[str] = []
    for line in lines:
        if line.startswith("NEXUS_TOOL_PACKAGES="):
            result.append(new_line)
            replaced = True
        else:
            result.append(line)
    if not replaced:
        if result and result[-1] != "":
            result.append("")
        result.append(new_line)

    if dry_run:
        return
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("\n".join(result) + "\n", encoding="utf-8")


def validate_generated_python(services: Sequence[ServiceSpec], dry_run: bool) -> None:
    if dry_run:
        return
    for service in services:
        for py_file in sorted(service.pack_root.rglob("*.py")):
            py_compile.compile(str(py_file), doraise=True)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    requested = [item.strip() for item in args.services.split(",") if item.strip()]
    services = discover_services(repo_root, requested)

    print(f"Target repo: {repo_root}")
    print("Services to migrate:")
    for service in services:
        print(f"- {service.name} -> {service.package_name}")

    all_warnings: List[str] = []
    for service in services:
        print(f"Preparing {service.pack_root}")
        all_warnings.extend(copy_service(service, dry_run=args.dry_run, force=args.force))

    package_names = [service.package_name for service in services]
    print(f"Recommended NEXUS_TOOL_PACKAGES={','.join(package_names)}")

    if args.update_env:
        env_file = Path(args.env_file).expanduser() if args.env_file else repo_root / ".env"
        print(f"Updating env file: {env_file}")
        update_env_file(env_file, package_names, args.dry_run)

    validate_generated_python(services, args.dry_run)

    if all_warnings:
        print("Warnings:")
        for warning in sorted(set(all_warnings)):
            print(f"- {warning}")

    if args.dry_run:
        print("Dry run complete. No files were written.")
    else:
        print("Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
