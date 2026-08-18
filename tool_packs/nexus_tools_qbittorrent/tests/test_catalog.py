from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

from nexus.tool_catalog import scan_package  # noqa: E402


def test_qbittorrent_tools_are_ast_discoverable() -> None:
    package_path = PACKAGE_ROOT / "nexus_tools_qbittorrent"
    specs = list(scan_package("nexus_tools_qbittorrent", package_path))
    names = {spec.name for spec in specs}

    assert len(specs) == 91
    assert "qbittorrent.app_get_version" in names
    assert "qbittorrent.torrent_add" in names
    assert "qbittorrent.torrent_delete" in names
    assert "qbittorrent.rss_set_rule" in names
    assert "qbittorrent.search_start" in names


def test_destructive_tools_have_write_class_and_explicit_descriptions() -> None:
    package_path = PACKAGE_ROOT / "nexus_tools_qbittorrent"
    specs = {spec.name: spec for spec in scan_package("nexus_tools_qbittorrent", package_path)}

    delete_tool = specs["qbittorrent.torrent_delete"]
    shutdown_tool = specs["qbittorrent.app_shutdown"]
    install_plugin_tool = specs["qbittorrent.search_install_plugin"]

    assert delete_tool.tool_class == "write"
    assert "downloaded data is also deleted" in delete_tool.description
    assert shutdown_tool.tool_class == "write"
    assert "stops the running server process" in shutdown_tool.description
    assert install_plugin_tool.tool_class == "write"
