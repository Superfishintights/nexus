"""Shared standard-library HTTP client for WAHA."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from nexus.config import get_setting


DEFAULT_LOCAL_FILE_MAX_BYTES = 64 * 1024 * 1024
HARD_LOCAL_FILE_MAX_BYTES = 128 * 1024 * 1024
_MIMETYPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+\-]*/[A-Za-z0-9][A-Za-z0-9!#$&^_.+\-]*(?:\s*;\s*[A-Za-z0-9!#$&^_.+\-]+=[A-Za-z0-9!#$&^_.+\-]+)*$")


class WahaAPIError(RuntimeError):
    """A sanitized WAHA HTTP error."""

    def __init__(self, status: int, method: str, path: str, detail: Any):
        self.status = status
        self.method = method
        self.path = path
        self.detail = detail
        super().__init__(f"WAHA {method} {path} failed with HTTP {status}: {detail}")


def _read_secret(value_name: str, file_name: str) -> str:
    direct = (get_setting(value_name) or "").strip()
    if direct:
        return direct

    path_value = (get_setting(file_name) or "").strip()
    if not path_value:
        return ""
    try:
        return Path(path_value).expanduser().read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError(f"Unable to read {file_name}: {exc}") from exc


def _timeout() -> float:
    raw = (get_setting("WAHA_TIMEOUT_S") or "").strip()
    if not raw:
        return 30.0
    try:
        return float(raw)
    except ValueError:
        return 30.0


def _local_file_max_bytes() -> int:
    raw = (get_setting("WAHA_LOCAL_FILE_MAX_BYTES") or "").strip()
    if not raw:
        return DEFAULT_LOCAL_FILE_MAX_BYTES
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("WAHA_LOCAL_FILE_MAX_BYTES must be an integer") from exc
    if value <= 0 or value > HARD_LOCAL_FILE_MAX_BYTES:
        raise ValueError(
            f"WAHA_LOCAL_FILE_MAX_BYTES must be between 1 and {HARD_LOCAL_FILE_MAX_BYTES}"
        )
    return value


def _safe_filename(filename: str) -> str:
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be a non-empty basename")
    if filename != Path(filename).name or filename in {".", ".."}:
        raise ValueError("filename must be a basename without directory components")
    if len(filename.encode("utf-8")) > 255:
        raise ValueError("filename must be at most 255 UTF-8 bytes")
    if any(ord(character) < 32 or ord(character) == 127 for character in filename):
        raise ValueError("filename must not contain control characters")
    return filename


def encode_local_file(
    path: str,
    *,
    filename: Optional[str] = None,
    mimetype: Optional[str] = None,
) -> Dict[str, str]:
    """Validate and encode one local regular file as a WAHA data URL."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty absolute local file path")
    source = Path(path)
    if not source.is_absolute():
        raise ValueError("path must be absolute")

    chosen_filename = _safe_filename(filename if filename is not None else source.name)
    chosen_mimetype = mimetype or mimetypes.guess_type(chosen_filename)[0] or "application/octet-stream"
    if not isinstance(chosen_mimetype, str) or not _MIMETYPE_RE.fullmatch(chosen_mimetype.strip()):
        raise ValueError("mimetype must be a valid MIME media type")
    chosen_mimetype = chosen_mimetype.strip()

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(source, flags)
    except OSError as exc:
        raise ValueError(f"unable to open local file: {exc}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("path must identify a regular file")
        limit = _local_file_max_bytes()
        if metadata.st_size <= 0:
            raise ValueError("local file must not be empty")
        if metadata.st_size > limit:
            raise ValueError(
                f"local file is {metadata.st_size} bytes; maximum allowed is {limit} bytes"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            content = handle.read(limit + 1)
        if len(content) > limit:
            raise ValueError(f"local file exceeds the maximum allowed size of {limit} bytes")
    finally:
        os.close(descriptor)

    encoded = base64.b64encode(content).decode("ascii")
    return {
        "data": encoded,
        "filename": chosen_filename,
        "mimetype": chosen_mimetype,
    }


class WahaClient:
    """Small JSON client for a private WAHA instance."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout_s: Optional[float] = None,
    ):
        self.base_url = (base_url or get_setting("WAHA_URL") or "").strip().rstrip("/")
        self.api_key = api_key or _read_secret("WAHA_API_KEY", "WAHA_API_KEY_FILE")
        self.timeout_s = timeout_s if timeout_s is not None else _timeout()
        if not self.base_url:
            raise ValueError("WAHA_URL is required")
        if not self.api_key:
            raise ValueError("WAHA_API_KEY or WAHA_API_KEY_FILE is required")

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        accept: str = "application/json",
    ) -> Any:
        return self.request("GET", path, params=params, accept=accept)

    def post(
        self,
        path: str,
        body: Optional[Any] = None,
        *,
        params: Optional[Dict[str, Any]] = None,
        accept: str = "application/json",
    ) -> Any:
        return self.request("POST", path, body=body, params=params, accept=accept)

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        accept: str = "application/json",
    ) -> Any:
        clean_path = "/" + path.lstrip("/")
        query = self._encode_params(params)
        url = f"{self.base_url}{clean_path}"
        if query:
            url = f"{url}?{query}"

        data = None
        headers = {"Accept": accept, "X-Api-Key": self.api_key}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read()
                return self._decode_response(raw, response.headers.get("Content-Type", ""), response.status)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            detail = self._decode_response(raw, exc.headers.get("Content-Type", ""), exc.code)
            raise WahaAPIError(exc.code, method.upper(), clean_path, detail) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"WAHA {method.upper()} {clean_path} connection failed: {exc.reason}") from exc

    @staticmethod
    def _encode_params(params: Optional[Dict[str, Any]]) -> str:
        if not params:
            return ""
        clean: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                clean[key] = "true" if value else "false"
            else:
                clean[key] = value
        return urllib.parse.urlencode(clean, doseq=True)

    @staticmethod
    def _decode_response(raw: bytes, content_type: str, status: int) -> Any:
        if not raw:
            return {"success": 200 <= status < 300, "status": status}
        text = raw.decode("utf-8", errors="replace")
        if "json" in content_type.lower() or text[:1] in ("{", "["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return {"status": status, "content_type": content_type, "text": text}


_default_client: Optional[WahaClient] = None
_default_client_key: Optional[tuple[str, str, float]] = None
_control_client: Optional[WahaClient] = None
_control_client_key: Optional[tuple[str, str, float]] = None


def get_client() -> WahaClient:
    """Return the cached session-scoped read/send client."""
    global _default_client, _default_client_key
    base_url = (get_setting("WAHA_URL") or "").strip().rstrip("/")
    api_key = _read_secret("WAHA_API_KEY", "WAHA_API_KEY_FILE")
    timeout_s = _timeout()
    key = (base_url, api_key, timeout_s)
    if _default_client is None or _default_client_key != key:
        _default_client = WahaClient(base_url=base_url, api_key=api_key, timeout_s=timeout_s)
        _default_client_key = key
    return _default_client


def get_control_client() -> WahaClient:
    """Return the cached session-scoped control client."""
    global _control_client, _control_client_key
    base_url = (get_setting("WAHA_URL") or "").strip().rstrip("/")
    api_key = _read_secret("WAHA_CONTROL_API_KEY", "WAHA_CONTROL_API_KEY_FILE")
    timeout_s = _timeout()
    if not api_key:
        raise ValueError("WAHA_CONTROL_API_KEY or WAHA_CONTROL_API_KEY_FILE is required")
    key = (base_url, api_key, timeout_s)
    if _control_client is None or _control_client_key != key:
        _control_client = WahaClient(base_url=base_url, api_key=api_key, timeout_s=timeout_s)
        _control_client_key = key
    return _control_client
