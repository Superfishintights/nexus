from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Tuple

from nexus import tool_catalog
from nexus.tool_registry import clear_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PACKS_ROOT = REPO_ROOT / "tool_packs"

CORE_PACKAGES: Tuple[str, ...] = (
    "nexus_tools_jira",
    "nexus_tools_n8n",
    "nexus_tools_radarr",
    "nexus_tools_sonarr",
    "nexus_tools_tautulli",
)
STARLING_PACKAGE = "nexus_tools_starling"


def add_tool_pack_paths(packages: Iterable[str]) -> None:
    for package_name in packages:
        package_root = TOOL_PACKS_ROOT / package_name
        if not package_root.exists():
            continue
        package_root_s = str(package_root)
        if package_root_s not in sys.path:
            sys.path.insert(0, package_root_s)


def builtin_tool_packages(*, include_starling: bool = False) -> Tuple[str, ...]:
    if include_starling:
        return CORE_PACKAGES + (STARLING_PACKAGE,)
    return CORE_PACKAGES


def configure_tool_packages(monkeypatch, package_names: Iterable[str]) -> Tuple[str, ...]:
    package_list = tuple(package_names)
    add_tool_pack_paths(package_list)
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, ",".join(package_list))
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()
    clear_registry()
    return package_list
