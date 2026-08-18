"""Compact, read-only Sonarr release search helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from nexus.tool_registry import register_tool

from .client import get_client


def _as_int(value: Any, name: str) -> int:
    if value is None:
        raise ValueError(f"{name} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _casefold(value: Any) -> str:
    return str(value or "").casefold()


def _iter_titles(series: Dict[str, Any]) -> Iterable[str]:
    title = series.get("title")
    if title:
        yield str(title)
    title_slug = series.get("titleSlug")
    if title_slug:
        yield str(title_slug)
    for alternate in series.get("alternateTitles") or []:
        if isinstance(alternate, dict) and alternate.get("title"):
            yield str(alternate["title"])


def _choose_series(candidates: Any, term: str) -> Optional[Dict[str, Any]]:
    if not isinstance(candidates, list):
        return None

    term_cf = _casefold(term)
    exact: list[Dict[str, Any]] = []
    partial: list[Dict[str, Any]] = []
    fallback: list[Dict[str, Any]] = []

    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("id") is None:
            continue
        fallback.append(candidate)
        titles = list(_iter_titles(candidate))
        if any(_casefold(title) == term_cf for title in titles):
            exact.append(candidate)
        elif any(term_cf in _casefold(title) for title in titles):
            partial.append(candidate)

    return (exact or partial or fallback or [None])[0]


def _resolve_series(client: Any, series_id: Any, series_title: Optional[str], query: Optional[str]) -> tuple[int, Optional[str]]:
    if series_id is not None:
        return _as_int(series_id, "series_id"), series_title or query

    term = series_title or query
    if not term:
        raise ValueError("Provide series_id or series_title/query")

    series = _choose_series(client.get("series"), term)
    if series is None:
        series = _choose_series(client.get("series/lookup", params={"term": term}), term)
    if series is None or series.get("id") is None:
        raise ValueError(f"No Sonarr series found for {term!r}")

    return _as_int(series["id"], "series_id"), series.get("title") or term


def _quality_parts(release: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[int]]:
    quality_model = release.get("quality")
    if not isinstance(quality_model, dict):
        return None, None, None

    quality = quality_model.get("quality")
    if not isinstance(quality, dict):
        return None, None, None

    return (
        quality.get("source"),
        quality.get("name"),
        quality.get("resolution"),
    )


def _human_size(size: Any) -> Optional[str]:
    if size is None:
        return None
    try:
        value = float(size)
    except (TypeError, ValueError):
        return None

    units = ("B", "KiB", "MiB", "GiB", "TiB")
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.2f} {units[unit_index]}"


def _compact_release(release: Dict[str, Any]) -> Dict[str, Any]:
    source, quality, resolution = _quality_parts(release)
    size = release.get("size")
    compact: Dict[str, Any] = {
        "title": release.get("title"),
        "releaseName": release.get("title"),
        "source": source,
        "quality": quality,
        "resolution": resolution,
        "customFormatScore": release.get("customFormatScore"),
        "size": size,
        "sizeHuman": _human_size(size),
        "indexer": release.get("indexer"),
        "fullSeason": release.get("fullSeason"),
        "rejected": release.get("rejected"),
        "rejections": release.get("rejections") or [],
        "downloadAllowed": release.get("downloadAllowed"),
    }

    for key in ("age", "ageHours", "ageMinutes", "seeders", "leechers", "protocol"):
        if release.get(key) is not None:
            compact[key] = release[key]

    return compact


def _matches_quality(release: Dict[str, Any], quality_contains: Optional[str]) -> bool:
    if not quality_contains:
        return True
    needle = quality_contains.casefold()
    source, quality, resolution = _quality_parts(release)
    haystack = " ".join(
        str(part)
        for part in (source, quality, resolution, release.get("title"))
        if part is not None
    ).casefold()
    return needle in haystack


def _score(release: Dict[str, Any]) -> int:
    value = release.get("customFormatScore")
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _seeders(release: Dict[str, Any]) -> int:
    value = release.get("seeders")
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


@register_tool(
    namespace="sonarr",
    description=(
        "Read-only Sonarr season release search that filters and compacts "
        "GET /api/v3/release results."
    ),
    examples=[
        (
            "load_tool(\"sonarr.list_season_releases\")("
            "series_title=\"Game of Thrones\", season_number=6, "
            "quality_contains=\"1080p\", positive_score_only=True)"
        ),
    ],
    tool_class="read",
    aliases=[],
)
def list_season_releases(
    series_id: Optional[int] = None,
    series_title: Optional[str] = None,
    query: Optional[str] = None,
    season_number: Optional[int] = None,
    quality_contains: Optional[str] = None,
    full_season_only: bool = True,
    min_custom_format_score: Optional[int] = None,
    positive_score_only: bool = False,
    max_results: Optional[int] = 50,
    include_rejected: bool = False,
    download_allowed: Optional[bool] = None,
) -> Dict[str, Any]:
    """List compact, filtered Sonarr release search results without grabbing."""

    client = get_client()
    resolved_series_id, resolved_title = _resolve_series(client, series_id, series_title, query)
    resolved_season_number = _as_int(season_number, "season_number")

    releases = client.get(
        "release",
        params={
            "seriesId": resolved_series_id,
            "seasonNumber": resolved_season_number,
        },
    )
    if not isinstance(releases, list):
        releases = []

    minimum_score = min_custom_format_score
    if positive_score_only and minimum_score is None:
        minimum_score = 1

    filtered: list[Dict[str, Any]] = []
    for release in releases:
        if not isinstance(release, dict):
            continue
        if full_season_only and release.get("fullSeason") is not True:
            continue
        if not include_rejected and release.get("rejected") is True:
            continue
        if download_allowed is not None and release.get("downloadAllowed") is not download_allowed:
            continue
        if minimum_score is not None and _score(release) < minimum_score:
            continue
        if not _matches_quality(release, quality_contains):
            continue
        filtered.append(release)

    filtered.sort(key=lambda release: (_score(release), _seeders(release)), reverse=True)

    result_limit = None if max_results is None else max(0, int(max_results))
    returned = filtered if result_limit is None else filtered[:result_limit]

    return {
        "seriesId": resolved_series_id,
        "seriesTitle": resolved_title,
        "seasonNumber": resolved_season_number,
        "totalReleases": len(releases),
        "totalFiltered": len(filtered),
        "returned": len(returned),
        "filters": {
            "qualityContains": quality_contains,
            "fullSeasonOnly": full_season_only,
            "minCustomFormatScore": minimum_score,
            "includeRejected": include_rejected,
            "downloadAllowed": download_allowed,
        },
        "releases": [_compact_release(release) for release in returned],
    }
