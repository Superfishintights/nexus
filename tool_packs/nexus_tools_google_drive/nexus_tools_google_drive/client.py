"""Drive-specific adapter over the shared Google client."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from nexus_tools_google_common.client import get_client as get_google_client
except Exception as exc:  # pragma: no cover - exercised only when dependency is missing.
    get_google_client = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

DRIVE_SERVICE = "drive"
UPLOAD_BASE_URL = "https://www.googleapis.com/upload/drive/v3"


def quote_segment(value: Any) -> str:
    return urllib.parse.quote(str(value), safe="")


def compact_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def coerce_body(body: Optional[Any]) -> Dict[str, Any]:
    if body is None:
        return {}
    if isinstance(body, dict):
        return dict(body)
    if isinstance(body, str):
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must decode to an object")
        return parsed
    raise ValueError("body must be a dict or JSON object string")


def coerce_list(value: Optional[Any]) -> Optional[List[Any]]:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.startswith("["):
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError("JSON value must decode to an array")
            return parsed
        return [raw]
    return [value]


class DriveClient:
    """Google Drive v3 client using the shared Google auth/session client."""

    def __init__(self, google_client: Optional[Any] = None):
        if google_client is not None:
            self.google_client = google_client
        else:
            if get_google_client is None:
                raise RuntimeError(
                    "nexus_tools_google_common.client.get_client is required for Google Drive tools"
                ) from _IMPORT_ERROR
            self.google_client = get_google_client()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        binary: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        client = self.google_client
        if hasattr(client, "request_json") and not binary:
            return client.request_json(DRIVE_SERVICE, path, method=method, params=params, body=body, headers=headers)
        if hasattr(client, "request_bytes") and binary:
            return client.request_bytes(DRIVE_SERVICE, path, method=method, params=params, body=body, headers=headers)
        if hasattr(client, "request"):
            try:
                return client.request(DRIVE_SERVICE, path, method=method, params=params, payload=body, binary=binary)
            except TypeError:
                return client.request(DRIVE_SERVICE, path, method=method, params=params, body=body, binary=binary)
        raise RuntimeError("Shared Google client must expose request_json/request_bytes or request")

    def upload_multipart(
        self,
        *,
        metadata: Dict[str, Any],
        content: bytes,
        mime_type: str,
        file_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        boundary = "nexus_drive_boundary_7f3c1b"
        body = b"".join(
            [
                f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode("utf-8"),
                json.dumps(metadata, separators=(",", ":")).encode("utf-8"),
                f"\r\n--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n".encode("utf-8"),
                content,
                f"\r\n--{boundary}--\r\n".encode("utf-8"),
            ]
        )
        path = "files" if file_id is None else f"files/{quote_segment(file_id)}"
        upload_params = compact_dict({**(params or {}), "uploadType": "multipart"})
        return self.request(
            "POST" if file_id is None else "PATCH",
            path,
            params=upload_params,
            body=body,
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )

    @staticmethod
    def read_content(*, content: Optional[str], content_base64: Optional[str], local_path: Optional[str]) -> bytes:
        supplied = [value is not None for value in (content, content_base64, local_path)].count(True)
        if supplied != 1:
            raise ValueError("Provide exactly one of content, content_base64, or local_path")
        if content is not None:
            return content.encode("utf-8")
        if content_base64 is not None:
            return base64.b64decode(content_base64)
        return Path(str(local_path)).read_bytes()

    @staticmethod
    def infer_mime_type(*, local_path: Optional[str], mime_type: Optional[str]) -> str:
        if mime_type:
            return mime_type
        if local_path:
            guessed, _ = mimetypes.guess_type(local_path)
            if guessed:
                return guessed
        return "application/octet-stream"

    @staticmethod
    def infer_name(*, local_path: Optional[str], name: Optional[str]) -> Optional[str]:
        if name:
            return name
        if local_path:
            return os.path.basename(local_path)
        return None


_default_client: Optional[DriveClient] = None


def get_client() -> DriveClient:
    global _default_client
    if _default_client is None:
        _default_client = DriveClient()
    return _default_client
