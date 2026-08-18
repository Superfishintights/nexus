from __future__ import annotations

import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PACK_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_ROOT))

from nexus import tool_catalog  # noqa: E402
from nexus_tools_sonarr import client as sonarr_client  # noqa: E402
from nexus_tools_sonarr import list_season_releases as season_releases  # noqa: E402


def _reset_client_cache() -> None:
    sonarr_client._default_client = None
    sonarr_client._default_client_key = None


def test_sonarr_timeout_env_is_used_and_part_of_client_cache(monkeypatch) -> None:
    _reset_client_cache()
    monkeypatch.setenv("SONARR_URL", "https://sonarr.example")
    monkeypatch.setenv("SONARR_API_KEY", "secret")
    monkeypatch.setenv("SONARR_TIMEOUT_S", "90")

    first = sonarr_client.get_client()
    second = sonarr_client.get_client()

    assert first.timeout_s == 90.0
    assert second is first

    monkeypatch.setenv("SONARR_TIMEOUT_S", "45")

    third = sonarr_client.get_client()

    assert third.timeout_s == 45.0
    assert third is not first


def test_list_season_releases_filters_and_compacts(monkeypatch) -> None:
    class FakeClient:
        def get(self, endpoint, params=None):  # noqa: ANN001
            if endpoint == "series":
                return [{"id": 220, "title": "Game of Thrones"}]
            if endpoint == "release":
                assert params == {"seriesId": 220, "seasonNumber": 6}
                return [
                    {
                        "title": "Game.of.Thrones.S06.1080p.BluRay-GROUP",
                        "quality": {
                            "quality": {
                                "name": "Bluray-1080p",
                                "source": "bluray",
                                "resolution": 1080,
                            }
                        },
                        "customFormatScore": 25,
                        "size": 5368709120,
                        "indexer": "Indexer A",
                        "fullSeason": True,
                        "rejected": False,
                        "downloadAllowed": True,
                        "age": 12,
                        "seeders": 14,
                    },
                    {
                        "title": "Game.of.Thrones.S06.720p.WEB-DL-GROUP",
                        "quality": {
                            "quality": {
                                "name": "WEBDL-720p",
                                "source": "webdl",
                                "resolution": 720,
                            }
                        },
                        "customFormatScore": 50,
                        "size": 100,
                        "indexer": "Indexer B",
                        "fullSeason": True,
                        "rejected": False,
                        "downloadAllowed": True,
                    },
                    {
                        "title": "Game.of.Thrones.S06E01.1080p.WEB-DL-GROUP",
                        "quality": {
                            "quality": {
                                "name": "WEBDL-1080p",
                                "source": "webdl",
                                "resolution": 1080,
                            }
                        },
                        "customFormatScore": 30,
                        "fullSeason": False,
                        "rejected": False,
                        "downloadAllowed": True,
                    },
                    {
                        "title": "Game.of.Thrones.S06.1080p.HDTV-GROUP",
                        "quality": {
                            "quality": {
                                "name": "HDTV-1080p",
                                "source": "television",
                                "resolution": 1080,
                            }
                        },
                        "customFormatScore": 0,
                        "fullSeason": True,
                        "rejected": False,
                        "downloadAllowed": True,
                    },
                    {
                        "title": "Game.of.Thrones.S06.1080p.Rejected-GROUP",
                        "quality": {
                            "quality": {
                                "name": "WEBDL-1080p",
                                "source": "webdl",
                                "resolution": 1080,
                            }
                        },
                        "customFormatScore": 40,
                        "fullSeason": True,
                        "rejected": True,
                        "rejections": ["Blocked release"],
                        "downloadAllowed": False,
                    },
                ]
            raise AssertionError(f"unexpected endpoint {endpoint}")

    monkeypatch.setattr(season_releases, "get_client", lambda: FakeClient())

    result = season_releases.list_season_releases(
        series_title="Game of Thrones",
        season_number=6,
        quality_contains="1080p",
        positive_score_only=True,
    )

    assert result["seriesId"] == 220
    assert result["totalReleases"] == 5
    assert result["totalFiltered"] == 1
    assert result["returned"] == 1
    assert result["releases"] == [
        {
            "title": "Game.of.Thrones.S06.1080p.BluRay-GROUP",
            "releaseName": "Game.of.Thrones.S06.1080p.BluRay-GROUP",
            "source": "bluray",
            "quality": "Bluray-1080p",
            "resolution": 1080,
            "customFormatScore": 25,
            "size": 5368709120,
            "sizeHuman": "5.00 GiB",
            "indexer": "Indexer A",
            "fullSeason": True,
            "rejected": False,
            "rejections": [],
            "downloadAllowed": True,
            "age": 12,
            "seeders": 14,
        }
    ]


def test_sonarr_list_season_releases_is_catalog_discoverable(monkeypatch) -> None:
    monkeypatch.syspath_prepend(str(PACK_ROOT))
    monkeypatch.setenv(tool_catalog.TOOL_PACKAGES_ENV, "nexus_tools_sonarr")
    tool_catalog._CATALOG = None
    tool_catalog._FILE_CACHE.clear()

    catalog = tool_catalog.get_catalog(refresh=True)

    assert "sonarr.list_season_releases" in catalog
    assert catalog["sonarr.list_season_releases"].tool_class == "read"
