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


def test_bazarr_catalog_discovers_representative_tools(monkeypatch) -> None:
    monkeypatch.syspath_prepend(str(PACK_ROOT))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "nexus_tools_bazarr")
    clear_registry()
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    catalog = tool_catalog.get_catalog(refresh=True)

    expected = {
        "bazarr.get_system_status",
        "bazarr.get_system_health",
        "bazarr.get_movies",
        "bazarr.update_movies_subtitles",
        "bazarr.create_episodes_subtitles",
        "bazarr.get_providers",
        "bazarr.update_system_jobs",
    }
    assert len(catalog) == 79
    assert expected.issubset(catalog)
    for name in expected:
        assert catalog[name].description
        assert catalog[name].examples
