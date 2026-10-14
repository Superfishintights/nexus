"""Shared, standard-library Chaptarr HTTP client. No requests at import time."""
from __future__ import annotations

import base64
import http.cookiejar
import json
import math
import mimetypes
from pathlib import Path
import re
from typing import Any, Dict, Optional
import urllib.error
import urllib.parse
import urllib.request
import uuid

from nexus.config import get_setting

DEFAULT_USER_AGENT = "NexusMCP/0.1 Chaptarr"


def quote_path(value: Any, catch_all: bool = False) -> str:
    """Encode an API path parameter, preserving slashes only for catch-all routes."""
    return urllib.parse.quote(str(value), safe="/" if catch_all else "")


def _read_api_key() -> Optional[str]:
    key = get_setting("CHAPTARR_API_KEY")
    if key:
        return key
    key_file = get_setting("CHAPTARR_API_KEY_FILE")
    if not key_file:
        return None
    try:
        return Path(key_file).read_text(encoding="utf-8").strip() or None
    except (OSError, UnicodeError):
        raise ValueError("Could not read CHAPTARR_API_KEY_FILE") from None


def _get_timeout_s() -> float:
    raw = get_setting("CHAPTARR_TIMEOUT_S")
    try:
        timeout = 30.0 if raw is None else float(raw)
    except (TypeError, ValueError):
        raise ValueError("CHAPTARR_TIMEOUT_S must be a number of seconds") from None
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("CHAPTARR_TIMEOUT_S must be a finite number greater than zero")
    return timeout


class _SameOriginRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not forward the API key or session authentication to another origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        original = urllib.parse.urlsplit(req.full_url)
        destination = urllib.parse.urlsplit(newurl)
        def origin(parsed):
            return (parsed.scheme.lower(), parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        if destination.username or destination.password or origin(original) != origin(destination):
            raise urllib.error.URLError("Refused redirect outside the configured Chaptarr origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class ChaptarrClient:
    """Read configuration lazily and share HTTP handling across Chaptarr tools."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 *, timeout_s: float = 30.0, api_path: str = "/api/v1"):
        base_url = base_url or get_setting("CHAPTARR_URL")
        self.api_key = api_key or _read_api_key()
        if not base_url:
            raise ValueError("CHAPTARR_URL is required")
        if not self.api_key:
            raise ValueError("CHAPTARR_API_KEY or CHAPTARR_API_KEY_FILE is required")
        if not base_url.startswith(("http://", "https://")):
            base_url = "https://" + base_url
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("CHAPTARR_URL must be an HTTP(S) base URL without credentials, query or fragment")
        self.base_url = base_url.rstrip("/")
        self.api_path = api_path
        self.timeout_s = float(timeout_s)
        if not math.isfinite(self.timeout_s) or self.timeout_s <= 0:
            raise ValueError("timeout_s must be a finite number greater than zero")
        self.cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            _SameOriginRedirectHandler(),
        )

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, body: Any = None, api_path: Optional[str] = None) -> Any:
        return self._request("GET", endpoint, params=params, body=body, api_path=api_path)

    def post(self, endpoint: str, body: Any = None, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None, files: Optional[list[dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", endpoint, params=params, body=body, api_path=api_path, files=files, form_data=form_data)

    def put(self, endpoint: str, body: Any = None, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None, files: Optional[list[dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PUT", endpoint, params=params, body=body, api_path=api_path, files=files, form_data=form_data)

    def patch(self, endpoint: str, body: Any = None, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None, files: Optional[list[dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("PATCH", endpoint, params=params, body=body, api_path=api_path, files=files, form_data=form_data)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, body: Any = None, api_path: Optional[str] = None) -> Any:
        return self._request("DELETE", endpoint, params=params, body=body, api_path=api_path)

    def head(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request("HEAD", endpoint, params=params, api_path=api_path)

    def _build_url(self, endpoint: str, api_path: Optional[str] = None) -> str:
        parsed = urllib.parse.urlsplit(endpoint)
        if parsed.scheme or parsed.netloc or parsed.fragment:
            raise ValueError("endpoint must be a relative API path without a fragment")
        endpoint_path = parsed.path.lstrip("/")
        if any(part in (".", "..") for part in urllib.parse.unquote(endpoint_path).split("/")):
            raise ValueError("endpoint cannot contain path traversal")
        chosen = self.api_path if api_path is None else api_path
        prefix = chosen.strip("/") if chosen else ""
        base = self.base_url
        default_suffix = "/" + self.api_path.strip("/")
        if default_suffix != "/" and base.endswith(default_suffix):
            base = base[:-len(default_suffix)]
        # Accept either resource paths or already-prefixed /api/v1 resource paths.
        if prefix and (endpoint_path == prefix or endpoint_path.startswith(prefix + "/")):
            prefix = ""
        path = "/".join(part for part in (prefix, endpoint_path) if part)
        url = base + ("/" + path if path else "")
        return url + ("?" + parsed.query if parsed.query else "")

    @staticmethod
    def _query(params: Optional[Dict[str, Any]]) -> str:
        values = []
        for key, value in (params or {}).items():
            for item in value if isinstance(value, (list, tuple)) else [value]:
                if item is not None:
                    values.append((key, "true" if item is True else "false" if item is False else str(item)))
        return urllib.parse.urlencode(values)

    @staticmethod
    def _multipart(files: list[dict[str, Any]], form_data: Dict[str, Any]) -> tuple[bytes, str]:
        boundary = "nexus-" + uuid.uuid4().hex
        chunks: list[bytes] = []
        def quoted(value: Any) -> str:
            text = str(value)
            if "\r" in text or "\n" in text:
                raise ValueError("Multipart field names and filenames cannot contain newlines")
            return text.replace("\\", "\\\\").replace('"', '\\"')
        for name, value in form_data.items():
            for item in value if isinstance(value, (list, tuple)) else [value]:
                if item is None:
                    continue
                text = "true" if item is True else "false" if item is False else str(item)
                chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{quoted(name)}"\r\n\r\n{text}\r\n').encode("utf-8"))
        for item in files:
            path_value = item.get("path") or item.get("local_path")
            if not path_value:
                raise ValueError("Each multipart file requires path or local_path")
            path = Path(path_value)
            filename = item.get("filename") or path.name
            field = item.get("field_name") or "files"
            content_type = item.get("content_type") or mimetypes.guess_type(str(filename))[0] or "application/octet-stream"
            if "\r" in content_type or "\n" in content_type:
                raise ValueError("Multipart content_type cannot contain newlines")
            try:
                content = path.read_bytes()
            except OSError:
                raise ValueError("Could not read a multipart upload file") from None
            chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{quoted(field)}"; filename="{quoted(filename)}"\r\nContent-Type: {content_type}\r\n\r\n').encode("utf-8") + content + b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode("ascii"))
        return b"".join(chunks), "multipart/form-data; boundary=" + boundary

    def _safe_error(self, detail: Any) -> str:
        text = str(detail).replace(self.api_key, "[redacted]")
        return re.sub(r"(?i)(api[-_]?key[=:\s]+)[^\s&,\"']+", r"\1[redacted]", text)[:2000]

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, body: Any = None, api_path: Optional[str] = None, *, files: Optional[list[dict[str, Any]]] = None, form_data: Optional[Dict[str, Any]] = None) -> Any:
        url = self._build_url(endpoint, api_path)
        query = self._query(params)
        if query:
            url += ("&" if "?" in url else "?") + query
        headers = {"X-Api-Key": self.api_key, "Accept": "application/json, application/octet-stream", "User-Agent": DEFAULT_USER_AGENT}
        data = None
        if files is not None:
            if body is not None:
                raise ValueError("Use form_data instead of body for multipart requests")
            data, headers["Content-Type"] = self._multipart(files or [], form_data or {})
        elif form_data is not None:
            if body is not None:
                raise ValueError("Use form_data instead of body for form requests")
            data = self._query(form_data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with self._opener.open(request, timeout=self.timeout_s) as response:
                if method == "HEAD":
                    return {"status_code": response.status, "headers": dict(response.headers.items())}
                raw = response.read()
                if not raw:
                    return None
                content_type = response.headers.get("Content-Type", "")
                media_type = content_type.split(";", 1)[0].strip().lower()
                is_text = media_type.startswith("text/") or "json" in media_type or "xml" in media_type or not media_type
                if is_text:
                    try:
                        decoded = raw.decode(response.headers.get_content_charset() or "utf-8")
                    except UnicodeDecodeError:
                        decoded = None
                    if decoded is not None:
                        try:
                            return json.loads(decoded)
                        except json.JSONDecodeError:
                            return decoded
                result = {"encoding": "base64", "data": base64.b64encode(raw).decode("ascii"), "content_type": content_type or "application/octet-stream", "size_bytes": len(raw)}
                if response.headers.get("Content-Disposition"):
                    result["content_disposition"] = response.headers["Content-Disposition"]
                return result
        except urllib.error.HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace") if exc.fp else ""
            raise RuntimeError(f"Chaptarr HTTP {exc.code}: {self._safe_error(detail)}") from None
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Chaptarr connection failed: {self._safe_error(exc.reason)}") from None
        except (TimeoutError, OSError) as exc:
            raise RuntimeError(f"Chaptarr request failed: {self._safe_error(exc)}") from None


_default_client: Optional[ChaptarrClient] = None
_default_client_key: Optional[tuple[str, str, float]] = None


def get_client() -> ChaptarrClient:
    """Refresh the cached client when URL, key-file contents or timeout change."""
    global _default_client, _default_client_key
    base_url = get_setting("CHAPTARR_URL") or ""
    api_key = _read_api_key() or ""
    timeout = _get_timeout_s()
    key = (base_url, api_key, timeout)
    if _default_client is None or _default_client_key != key:
        _default_client = ChaptarrClient(base_url=base_url, api_key=api_key, timeout_s=timeout)
        _default_client_key = key
    return _default_client
