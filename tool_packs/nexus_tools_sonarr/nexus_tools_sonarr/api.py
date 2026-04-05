"""Backward-compatible Sonarr convenience wrappers.

These wrappers are intentionally not registered tools. They preserve older
call patterns while delegating to canonical generated Sonarr tool functions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .client import get_client
from .create_command import create_command as _create_command
from .create_series import create_series as _create_series
from .delete_series_by_id import delete_series_by_id as _delete_series_by_id
from .get_qualityprofile import get_qualityprofile as _get_qualityprofile
from .get_rootfolder import get_rootfolder as _get_rootfolder
from .get_series import get_series as _get_series
from .get_series_by_id import get_series_by_id as _get_series_by_id
from .get_series_lookup import get_series_lookup as _get_series_lookup
from .update_series_by_id import update_series_by_id as _update_series_by_id

__all__ = [
    "get_client",
    "lookup_series",
    "add_series",
    "update_series",
    "delete_series",
    "run_command",
    "get_root_folders",
    "get_quality_profiles",
    "get_series",
]


def lookup_series(term: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Any:
    """Legacy wrapper for series lookup by term."""
    merged_params = dict(params or {})
    if term is not None and "term" not in merged_params:
        merged_params["term"] = term
    return _get_series_lookup(params=merged_params or None)


def add_series(series: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    """Legacy wrapper for adding a series."""
    return _create_series(params=params, body=series)


def update_series(
    series_id: Any,
    series: Any,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """Legacy wrapper for updating a series by id."""
    return _update_series_by_id(id=series_id, params=params, body=series)


def delete_series(
    series_id: Any,
    delete_files: bool = False,
    add_import_list_exclusion: bool = False,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """Legacy wrapper for deleting a series by id."""
    merged_params = dict(params or {})
    merged_params.setdefault("deleteFiles", delete_files)
    merged_params.setdefault("addImportListExclusion", add_import_list_exclusion)
    return _delete_series_by_id(id=series_id, params=merged_params or None)


def run_command(
    name: str,
    command_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Any:
    """Legacy wrapper for posting a command payload."""
    body: Dict[str, Any] = {"name": name}
    if command_body:
        body.update(command_body)
    if kwargs:
        body.update(kwargs)
    return _create_command(params=params, body=body)


def get_root_folders(params: Optional[Dict[str, Any]] = None) -> Any:
    """Legacy wrapper for root folder listing."""
    return _get_rootfolder(params=params)


def get_quality_profiles(params: Optional[Dict[str, Any]] = None) -> Any:
    """Legacy wrapper for quality profile listing."""
    return _get_qualityprofile(params=params)


def get_series(
    series_id: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """Legacy wrapper for list/get series."""
    if series_id is None:
        return _get_series(params=params)
    return _get_series_by_id(id=series_id, params=params)
