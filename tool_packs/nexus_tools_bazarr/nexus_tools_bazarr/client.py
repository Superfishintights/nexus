"""Shared Bazarr HTTP client for all Bazarr tools."""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)


class BazarrClient:
    """Simple Bazarr API client using only the standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout_s: Optional[float] = None,
        api_path: Optional[str] = None,
    ):
        self.base_url = base_url or get_setting("BAZARR_URL")
        self.api_key = api_key or get_setting("BAZARR_API_KEY")
        self.timeout_s = float(timeout_s if timeout_s is not None else (get_setting("BAZARR_TIMEOUT_S") or 30.0))
        self.api_path = api_path if api_path is not None else (get_setting("BAZARR_API_PATH") or "/api")

        if not self.base_url:
            raise ValueError("BAZARR_URL is required (set env var or put it in a `.env` file).")
        if not self.api_key:
            raise ValueError("BAZARR_API_KEY is required (set env var or put it in a `.env` file).")
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"http://{self.base_url}"
        self.base_url = self.base_url.rstrip("/")

    def get(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, body: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("POST", endpoint, params=params, body=body)

    def patch(self, endpoint: str, body: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("PATCH", endpoint, params=params, body=body)

    def put(self, endpoint: str, body: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("PUT", endpoint, params=params, body=body)

    def delete(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("DELETE", endpoint, params=params)

    def head(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("HEAD", endpoint, params=params)

    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip("/")
        path_prefix = self.api_path.strip("/") if self.api_path else ""
        url = self.base_url
        if path_prefix:
            url = f"{url}/{path_prefix}"
        if endpoint:
            url = f"{url}/{endpoint}"
        return url

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[Any] = None,
    ) -> Any:
        url = self._build_url(endpoint)
        query = _encode_params(params)
        if query:
            url = f"{url}?{query}"

        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json, text/plain, */*",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        data: Optional[bytes] = None

        if body is not None:
            data, content_type = _encode_body(body)
            headers["Content-Type"] = content_type
        elif method in {"POST", "PUT", "PATCH"}:
            headers["Content-Type"] = "application/json"

        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw_data = response.read()
                if method == "HEAD" or not raw_data:
                    return None
                response_data = raw_data.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
                content_type = response.headers.get("Content-Type", "").lower()
                if "json" in content_type:
                    try:
                        return json.loads(response_data)
                    except json.JSONDecodeError:
                        return response_data
                try:
                    return json.loads(response_data)
                except json.JSONDecodeError:
                    return response_data
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc


def _encode_body(body: Any) -> Tuple[bytes, str]:
    if isinstance(body, bytes):
        return body, "application/octet-stream"
    if isinstance(body, str):
        return body.encode("utf-8"), "text/plain; charset=utf-8"
    if isinstance(body, Mapping) and ("files" in body or "file" in body):
        fields = body.get("fields", {})
        if not isinstance(fields, Mapping):
            raise ValueError("multipart body field 'fields' must be a mapping")
        file_spec = body.get("files", body.get("file"))
        return _encode_multipart(fields, file_spec)
    return json.dumps(body).encode("utf-8"), "application/json"


def _encode_params(params: Optional[Mapping[str, Any]]) -> str:
    if not params:
        return ""
    query: Dict[str, Union[str, list[str]]] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            query[key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            values = [_stringify(item) for item in value if item is not None]
            if values:
                query[key] = values
        else:
            query[key] = _stringify(value)
    return urllib.parse.urlencode(query, doseq=True)


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def _encode_multipart(fields: Mapping[str, Any], file_spec: Any) -> Tuple[bytes, str]:
    boundary = f"----NexusBazarr{secrets.token_hex(16)}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        if value is None:
            continue
        chunks.extend([
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
            _stringify(value).encode("utf-8"),
            b"\r\n",
        ])

    for field_name, file_path in _normalize_files(file_spec):
        path = Path(file_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.extend([
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'
                f"Content-Type: {mime_type}\r\n\r\n"
            ).encode("utf-8"),
            path.read_bytes(),
            b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _normalize_files(file_spec: Any) -> list[tuple[str, os.PathLike[str] | str]]:
    if isinstance(file_spec, (str, os.PathLike)):
        return [("file", file_spec)]
    if isinstance(file_spec, Mapping):
        return [(str(name), path) for name, path in file_spec.items()]
    if isinstance(file_spec, (list, tuple)):
        normalized: list[tuple[str, os.PathLike[str] | str]] = []
        for item in file_spec:
            if isinstance(item, (str, os.PathLike)):
                normalized.append(("file", item))
            else:
                field_name, path = item
                normalized.append((str(field_name), path))
        return normalized
    raise ValueError("multipart body requires 'file' or 'files' as a path, mapping, or sequence")


_default_client: Optional[BazarrClient] = None
_default_client_key: Optional[tuple[str, str, str, str]] = None


def get_client() -> BazarrClient:
    """Get or create the default Bazarr client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("BAZARR_URL") or ""
    api_key = get_setting("BAZARR_API_KEY") or ""
    timeout = get_setting("BAZARR_TIMEOUT_S") or "30.0"
    api_path = get_setting("BAZARR_API_PATH") or "/api"
    key = (base_url, api_key, timeout, api_path)
    if _default_client is None or _default_client_key != key:
        _default_client = BazarrClient(base_url=base_url, api_key=api_key, timeout_s=float(timeout), api_path=api_path)
        _default_client_key = key
    return _default_client
