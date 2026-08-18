"""Shared SABnzbd HTTP client for all SABnzbd tools."""

from __future__ import annotations

import json
import mimetypes
import os
import uuid
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, Mapping, Optional

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)


class SabnzbdClient:
    """Simple SABnzbd mode/query API client using only standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout_s: Optional[float] = None,
        api_path: Optional[str] = None,
    ):
        self.base_url = base_url or get_setting("SABNZBD_URL")
        self.api_key = api_key or get_setting("SABNZBD_API_KEY")
        self.timeout_s = float(timeout_s or get_setting("SABNZBD_TIMEOUT_S") or 30.0)
        self.api_path = api_path or get_setting("SABNZBD_API_PATH") or "/api"

        if not self.base_url:
            raise ValueError(
                "SABNZBD_URL is required (set env var or put it in a `.env` file)."
            )
        if not self.api_key:
            raise ValueError(
                "SABNZBD_API_KEY is required (set env var or put it in a `.env` file)."
            )

        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"http://{self.base_url}"

        self.base_url = self.base_url.rstrip("/")
        self.api_path = "/" + self.api_path.strip("/") if self.api_path else "/api"

    def build_url(
        self,
        mode: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        include_api_key: bool = True,
        output: Optional[str] = "json",
    ) -> str:
        query = self._query(mode, params, include_api_key=include_api_key, output=output)
        return f"{self.base_url}{self.api_path}?{urllib.parse.urlencode(query, doseq=True)}"

    def call(
        self,
        mode: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        include_api_key: bool = True,
        output: Optional[str] = "json",
    ) -> Any:
        url = self.build_url(mode, params, include_api_key=include_api_key, output=output)
        return self._request(url)

    def upload_file(
        self,
        mode: str,
        file_path: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        file_field: str = "nzbfile",
    ) -> Any:
        query = self._query(mode, params, include_api_key=True, output="json")
        url = f"{self.base_url}{self.api_path}"
        body, content_type = self._multipart_body(query, file_path, file_field=file_field)
        headers = {
            "Accept": "application/json",
            "Content-Type": content_type,
            "User-Agent": DEFAULT_USER_AGENT,
        }
        return self._request(url, data=body, headers=headers)

    def _query(
        self,
        mode: str,
        params: Optional[Mapping[str, Any]],
        *,
        include_api_key: bool,
        output: Optional[str],
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"mode": mode}
        if output:
            query["output"] = output
        if include_api_key:
            query["apikey"] = self.api_key
        if params:
            for key, value in params.items():
                if value is None:
                    continue
                if isinstance(value, bool):
                    query[key] = "1" if value else "0"
                elif isinstance(value, (list, tuple, set)):
                    query[key] = ",".join(str(item) for item in value if item is not None)
                else:
                    query[key] = value
        return query

    def _request(
        self,
        url: str,
        *,
        data: Optional[bytes] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        request_headers = {
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if headers:
            request_headers.update(headers)

        try:
            request = urllib.request.Request(url, data=data, headers=request_headers)
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw_data = response.read()
                if not raw_data:
                    return None
                charset_getter = getattr(response.headers, "get_content_charset", None)
                charset = charset_getter() if charset_getter else None
                text = raw_data.decode(charset or "utf-8")
                content_type = response.headers.get("Content-Type", "").lower()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}") from exc

        if "json" in content_type:
            return self._loads_json(text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _loads_json(self, text: str) -> Any:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise Exception("Invalid JSON from SABnzbd API") from exc

        if isinstance(payload, dict) and "error" in payload:
            raise Exception(f"SABnzbd API error: {payload['error']}")
        return payload

    def _multipart_body(
        self,
        fields: Mapping[str, Any],
        file_path: str,
        *,
        file_field: str,
    ) -> tuple[bytes, str]:
        boundary = f"----NexusSabnzbd{uuid.uuid4().hex}"
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        chunks: list[bytes] = []
        for key, value in fields.items():
            if value is None:
                continue
            chunks.extend(
                [
                    f"--{boundary}\r\n".encode("utf-8"),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                    f"{value}\r\n".encode("utf-8"),
                ]
            )

        with open(file_path, "rb") as handle:
            file_bytes = handle.read()
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{file_field}"; '
                    f'filename="{filename}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                file_bytes,
                b"\r\n",
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
        )
        return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def csv(value: str | Iterable[str]) -> str:
    """Return SABnzbd's comma-separated identifier format."""
    if isinstance(value, str):
        return value
    return ",".join(str(item) for item in value)


def nzb_options(
    *,
    nzbname: Optional[str] = None,
    password: Optional[str] = None,
    cat: Optional[str] = None,
    script: Optional[str] = None,
    priority: Optional[int] = None,
    pp: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "nzbname": nzbname,
        "password": password,
        "cat": cat,
        "script": script,
        "priority": priority,
        "pp": pp,
    }


_default_client: Optional[SabnzbdClient] = None
_default_client_key: Optional[tuple[str, str, str, str]] = None


def get_client() -> SabnzbdClient:
    """Get or create the default SABnzbd client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("SABNZBD_URL") or ""
    api_key = get_setting("SABNZBD_API_KEY") or ""
    timeout_s = get_setting("SABNZBD_TIMEOUT_S") or ""
    api_path = get_setting("SABNZBD_API_PATH") or "/api"
    if not base_url or not api_key:
        _default_client = None
        _default_client_key = None
        return SabnzbdClient(base_url=base_url, api_key=api_key)

    new_key = (base_url, api_key, timeout_s, api_path)
    if _default_client is None or _default_client_key != new_key:
        _default_client = SabnzbdClient(
            base_url=base_url,
            api_key=api_key,
            timeout_s=float(timeout_s) if timeout_s else None,
            api_path=api_path,
        )
        _default_client_key = new_key
    return _default_client
