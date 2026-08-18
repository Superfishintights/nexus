from __future__ import annotations

import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_ROOT))

from nexus import tool_catalog
from nexus.tool_registry import clear_registry


def test_sabnzbd_catalog_discovers_representative_tools(monkeypatch) -> None:
    monkeypatch.syspath_prepend(str(PACK_ROOT))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "nexus_tools_sabnzbd")
    clear_registry()
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    catalog = tool_catalog.get_catalog(refresh=True)

    expected = {
        "sabnzbd.call",
        "sabnzbd.get_queue",
        "sabnzbd.add_url",
        "sabnzbd.get_history",
        "sabnzbd.get_status",
        "sabnzbd.get_config",
        "sabnzbd.shutdown",
    }
    assert expected.issubset(catalog)
    for name in expected:
        assert catalog[name].description
        assert catalog[name].examples
