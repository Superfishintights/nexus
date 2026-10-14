"""Helpers for Google Slides tool inputs and response summaries."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional


def coerce_dict(value: Any, *, name: str = "value") -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError(f"{name} must be a JSON object")
        return parsed
    if isinstance(value, dict):
        return value
    raise ValueError(f"{name} must be a mapping or JSON object string")


def coerce_list(value: Any, *, name: str = "value") -> List[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, list):
            raise ValueError(f"{name} must be a JSON array")
        return parsed
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    raise ValueError(f"{name} must be a list or JSON array string")


def drop_none(values: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def dimension(magnitude: float, unit: str = "PT") -> Dict[str, Any]:
    return {"magnitude": magnitude, "unit": unit}


def size(width: float, height: float, unit: str = "PT") -> Dict[str, Any]:
    return {"width": dimension(width, unit), "height": dimension(height, unit)}


def transform(
    *,
    translate_x: float = 0,
    translate_y: float = 0,
    scale_x: float = 1,
    scale_y: float = 1,
    shear_x: float = 0,
    shear_y: float = 0,
    unit: str = "PT",
) -> Dict[str, Any]:
    return {
        "scaleX": scale_x,
        "scaleY": scale_y,
        "shearX": shear_x,
        "shearY": shear_y,
        "translateX": translate_x,
        "translateY": translate_y,
        "unit": unit,
    }


def object_ids(presentation: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for slide in presentation.get("slides", []):
        if slide.get("objectId"):
            ids.append(slide["objectId"])
        for element in slide.get("pageElements", []):
            if element.get("objectId"):
                ids.append(element["objectId"])
    return ids


def text_runs(page_or_presentation: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages: Iterable[Dict[str, Any]]
    if "slides" in page_or_presentation:
        pages = page_or_presentation.get("slides", [])
    else:
        pages = [page_or_presentation]
    runs: List[Dict[str, Any]] = []
    for page in pages:
        page_id = page.get("objectId")
        for element in page.get("pageElements", []):
            shape = element.get("shape") or {}
            text = shape.get("text") or {}
            for item in text.get("textElements", []):
                run = item.get("textRun")
                if run:
                    runs.append(
                        {
                            "pageObjectId": page_id,
                            "objectId": element.get("objectId"),
                            "content": run.get("content"),
                            "style": run.get("style", {}),
                        }
                    )
    return runs


def normalize_requests(requests: Any) -> List[Dict[str, Any]]:
    values = coerce_list(requests, name="requests")
    normalized: List[Dict[str, Any]] = []
    for index, request in enumerate(values):
        if not isinstance(request, dict):
            raise ValueError(f"requests[{index}] must be an object")
        if len(request) != 1:
            raise ValueError(f"requests[{index}] must contain exactly one request type")
        normalized.append(request)
    return normalized


def singleton_request(request_type: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return {request_type: drop_none(body)}
