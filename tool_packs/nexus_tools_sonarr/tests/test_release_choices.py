"""Check the running release's compact, read-only comparison contract."""
from unittest.mock import Mock, patch

from nexus_tools_sonarr.list_season_releases import list_season_releases


def test_compact_candidates_keep_rejection_evidence_without_download_secrets():
    release = {
        "title": "Example.S01.1080p.WEB-DL", "fullSeason": True,
        "guid": "release-123", "indexerId": 2,
        "indexer": "Example Indexer", "infoUrl": "https://example.org/details/123",
        "downloadUrl": "https://example.org/download?apikey=private",
        "rejected": True, "rejections": ["Existing file meets cutoff"],
        "downloadAllowed": True, "customFormatScore": 75,
    }
    client = Mock()
    client.get.return_value = [release]
    with patch("nexus_tools_sonarr.list_season_releases.get_client", return_value=client):
        result = list_season_releases(series_id=143, season_number=1, include_rejected=True)
        assert result["returned"] == 1
        row = result["releases"][0]
        for key in ("title", "indexer", "customFormatScore", "rejections", "downloadAllowed"):
            assert row[key] == release[key]
        assert row["releaseName"] == release["title"]
        assert "downloadUrl" not in row
        assert list_season_releases(series_id=143, season_number=1)["returned"] == 0
    client.get.assert_called_with("release", params={"seriesId": 143, "seasonNumber": 1})
