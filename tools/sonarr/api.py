"""Sonarr API tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="sonarr",
    description="Get all series or a specific series by ID.",
    examples=["sonarr.get_series()", "sonarr.get_series(series_id=1)"],
)
def get_series(series_id: Optional[int] = None) -> Any:
    """Get all series or a specific series by ID.
    
    Args:
        series_id: Optional series ID to retrieve a single series.
    """
    client = get_client()
    if series_id is not None:
        return client.get(f"series/{series_id}")
    return client.get("series")


@register_tool(
    namespace="sonarr",
    description="Search for a series by name (lookup).",
    examples=["sonarr.lookup_series('Breaking Bad')"],
)
def lookup_series(term: str) -> List[Dict[str, Any]]:
    """Search for a series by name (using the 'term' parameter for lookup)."""
    return get_client().get("series/lookup", params={"term": term})


@register_tool(
    namespace="sonarr",
    description="Add a new series to Sonarr.",
    examples=['sonarr.add_series(tvdb_id=121361, title="Game of Thrones", root_folder_path="/tv", quality_profile_id=1)'],
)
def add_series(
    tvdb_id: int,
    title: str,
    root_folder_path: str,
    quality_profile_id: int,
    monitored: bool = True,
    search_for_missing_episodes: bool = False,
    season_folder: bool = True,
    tags: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Add a new series to Sonarr.

    Args:
        tvdb_id: The TVDB ID of the series.
        title: The title of the series.
        root_folder_path: Full path to where the series should be stored (e.g. "/tv").
        quality_profile_id: ID of the quality profile to use.
        monitored: Whether to monitor the series (default: True).
        search_for_missing_episodes: Start a search for missing episodes immediately (default: False).
        season_folder: Create season folders (default: True).
        tags: Optional list of tag IDs.
    """
    body = {
        "tvdbId": tvdb_id,
        "title": title,
        "rootFolderPath": root_folder_path,
        "qualityProfileId": quality_profile_id,
        "monitored": monitored,
        "seasonFolder": season_folder,
        "tags": tags or [],
        "addOptions": {
            "searchForMissingEpisodes": search_for_missing_episodes,
        },
    }
    return get_client().post("series", body=body)


@register_tool(
    namespace="sonarr",
    description="Update an existing series (e.g. change profile or path).",
    examples=['sonarr.update_series(series_id=1, monitored=False)'],
)
def update_series(series_id: int, **kwargs: Any) -> Dict[str, Any]:
    """Update an existing series.

    First fetches the series to get the current state, merges `kwargs` into it,
    and sends it back.

    Args:
        series_id: The ID of the series to update.
        **kwargs: Fields to update (e.g., monitored=False, qualityProfileId=2).
    """
    client = get_client()
    # 1. Fetch current series data
    current = client.get(f"series/{series_id}")
    
    # 2. Update fields
    # Note: simple top-level merge. Complex nested updates might need more logic.
    current.update(kwargs)
    
    # 3. PUT back
    return client.put(f"series/{series_id}", body=current)


@register_tool(
    namespace="sonarr",
    description="Delete a series.",
    examples=['sonarr.delete_series(series_id=1, delete_files=True)'],
)
def delete_series(
    series_id: int,
    delete_files: bool = False,
    add_import_list_exclusion: bool = False,
) -> Any:
    """Delete a series.

    Args:
        series_id: The ID of the series to delete.
        delete_files: Whether to delete the series files from disk (default: False).
        add_import_list_exclusion: Whether to add an exclusion to prevent auto-reimport (default: False).
    """
    params = {
        "deleteFiles": delete_files,
        "addImportListExclusion": add_import_list_exclusion,
    }
    return get_client().delete(f"series/{series_id}", params=params)


@register_tool(
    namespace="sonarr",
    description="Get current download queue.",
    examples=["sonarr.get_queue()"],
)
def get_queue(
    page: int = 1,
    page_size: int = 20,
    sort_key: str = "timeLeft",
    sort_direction: str = "ascending",
    include_unknown_series_items: bool = False,
) -> Dict[str, Any]:
    """Get the current download queue."""
    return get_client().get(
        "queue",
        params={
            "page": page,
            "pageSize": page_size,
            "sortKey": sort_key,
            "sortDirection": sort_direction,
            "includeUnknownSeriesItems": include_unknown_series_items,
        },
    )


@register_tool(
    namespace="sonarr",
    description="Get history (grabs/imports/failures).",
    examples=["sonarr.get_history()", "sonarr.get_history(page_size=5)"],
)
def get_history(
    page: int = 1,
    page_size: int = 20,
    sort_key: str = "date",
    sort_direction: str = "descending",
    event_type: Optional[int] = None,
) -> Dict[str, Any]:
    """Get history.
    
    Args:
        page: Page number (1-based).
        page_size: Number of records per page.
        sort_key: Field to sort by (default 'date').
        sort_direction: 'ascending' or 'descending'.
        event_type: Optional filter (1=Grabbed, 3=DownloadFolderImported, etc).
    """
    params = {
        "page": page,
        "pageSize": page_size,
        "sortKey": sort_key,
        "sortDirection": sort_direction,
    }
    if event_type is not None:
        params["eventType"] = event_type
    
    return get_client().get("history", params=params)


@register_tool(
    namespace="sonarr",
    description="Get root folders (paths where series are stored).",
    examples=["sonarr.get_root_folders()"],
)
def get_root_folders() -> List[Dict[str, Any]]:
    """Get root folders."""
    return get_client().get("rootfolder")


@register_tool(
    namespace="sonarr",
    description="Get quality profiles.",
    examples=["sonarr.get_quality_profiles()"],
)
def get_quality_profiles() -> List[Dict[str, Any]]:
    """Get quality profiles."""
    return get_client().get("qualityprofile")


@register_tool(
    namespace="sonarr",
    description="Execute a command (e.g., SeriesSearch, RefreshSeries).",
    examples=['sonarr.run_command("SeriesSearch", seriesId=1)'],
)
def run_command(name: str, **kwargs: Any) -> Dict[str, Any]:
    """Execute a command.
    
    Common commands:
    - SeriesSearch (requires seriesId)
    - EpisodeSearch (requires episodeIds=[...])
    - RefreshSeries (requires seriesId or nothing for all)
    - Backup
    - DownloadedEpisodesScan (requires path)
    """
    body = {"name": name, **kwargs}
    return get_client().post("command", body=body)