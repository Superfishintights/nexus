"""Shared qBittorrent WebUI API client."""

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)


class QBittorrentClient:
    """Simple qBittorrent WebUI API client using only standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        timeout_s: Optional[float] = None,
        api_path: Optional[str] = None,
    ):
        self.base_url = base_url or get_setting("QBITTORRENT_URL")
        self.username = username or get_setting("QBITTORRENT_USERNAME")
        self.password = password or get_setting("QBITTORRENT_PASSWORD")
        self.timeout_s = float(timeout_s if timeout_s is not None else (get_setting("QBITTORRENT_TIMEOUT_S") or 30.0))
        self.api_path = api_path if api_path is not None else (get_setting("QBITTORRENT_API_PATH") or "/api/v2")
        self._sid: Optional[str] = None
        self._sid_cookie_name: Optional[str] = None

        if not self.base_url:
            raise ValueError("QBITTORRENT_URL is required")
        if not self.username or not self.password:
            raise ValueError("QBITTORRENT_USERNAME and QBITTORRENT_PASSWORD are required")
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"http://{self.base_url}"
        self.base_url = self.base_url.rstrip("/")

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """Log in and store the returned SID cookie."""
        user = username or self.username
        pwd = password or self.password
        if not user or not pwd:
            raise ValueError("username and password are required")
        text, headers = self._request_raw(
            "POST",
            "auth/login",
            form={"username": user, "password": pwd},
            authenticated=False,
        )
        sid_cookie = _extract_sid_cookie_from_headers(headers)
        if sid_cookie:
            self._sid_cookie_name, self._sid = sid_cookie
        else:
            self._sid_cookie_name = None
            self._sid = None
        if not self._sid:
            status = text.strip()
            if status == "Fails.":
                raise Exception("qBittorrent authentication failed: invalid username or password.")
            raise Exception(
                "qBittorrent authentication failed: login response did not include a SID cookie. "
                "Check credentials, reverse proxy/Authelia routing, and qBittorrent WebUI host/CSRF settings."
            )
        return {"status": text, "sid": self._sid}

    def logout(self) -> Any:
        result = self.post("auth/logout")
        self._sid = None
        self._sid_cookie_name = None
        return result

    def get(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Mapping[str, Any]] = None) -> Any:
        return self._request("POST", endpoint, form=data)

    def post_json_field(self, endpoint: str, field_name: str, payload: Any) -> Any:
        value = payload if isinstance(payload, str) else json.dumps(payload, separators=(",", ":"))
        return self.post(endpoint, {field_name: value})

    def post_multipart(
        self,
        endpoint: str,
        fields: Optional[Mapping[str, Any]] = None,
        files: Optional[Sequence[Union[str, os.PathLike[str]]]] = None,
    ) -> Any:
        body, content_type = _encode_multipart(fields or {}, files or ())
        return self._request("POST", endpoint, body=body, content_type=content_type)

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        form: Optional[Mapping[str, Any]] = None,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> Any:
        text, headers = self._request_raw(
            method,
            endpoint,
            params=params,
            form=form,
            body=body,
            content_type=content_type,
            authenticated=True,
        )
        if text == "":
            return None
        response_type = headers.get("Content-Type", "").lower()
        if "json" in response_type:
            return json.loads(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        form: Optional[Mapping[str, Any]] = None,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
        authenticated: bool,
        retry_login: bool = True,
    ) -> Tuple[str, Mapping[str, str]]:
        if authenticated and not self._sid:
            self.login()

        url = self._build_url(endpoint)
        query = _encode_params(params)
        if query:
            url = f"{url}?{query}"

        data = body
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": self.base_url + "/",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if authenticated and self._sid:
            headers["Cookie"] = f"{self._sid_cookie_name or 'SID'}={self._sid}"
        if form is not None:
            data = _encode_params(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif content_type is not None:
            headers["Content-Type"] = content_type

        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                return raw.decode(charset), response.headers
        except urllib.error.HTTPError as exc:
            if authenticated and exc.code == 403 and retry_login:
                self._sid = None
                self._sid_cookie_name = None
                self.login()
                return self._request_raw(
                    method,
                    endpoint,
                    params=params,
                    form=form,
                    body=body,
                    content_type=content_type,
                    authenticated=authenticated,
                    retry_login=False,
                )
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {detail}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc

    def _build_url(self, endpoint: str) -> str:
        path_prefix = self.api_path.strip("/") if self.api_path else ""
        endpoint = endpoint.lstrip("/")
        url = self.base_url
        if path_prefix:
            url = f"{url}/{path_prefix}"
        if endpoint:
            url = f"{url}/{endpoint}"
        return url


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
            query[key] = [_stringify(item) for item in value if item is not None]
        else:
            query[key] = _stringify(value)
    return urllib.parse.urlencode(query, doseq=True)


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def _extract_sid(cookie_header: str) -> Optional[str]:
    cookie = _extract_sid_cookie(cookie_header)
    return cookie[1] if cookie else None


def _extract_sid_cookie(cookie_header: str) -> Optional[tuple[str, str]]:
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        if name == "SID" or name.startswith("QBT_SID"):
            return (name, value) if value else None
    return None


def _extract_sid_from_headers(headers: Mapping[str, str]) -> Optional[str]:
    cookie = _extract_sid_cookie_from_headers(headers)
    return cookie[1] if cookie else None


def _extract_sid_cookie_from_headers(headers: Mapping[str, str]) -> Optional[tuple[str, str]]:
    get_all = getattr(headers, "get_all", None)
    cookie_headers = get_all("Set-Cookie") if callable(get_all) else None
    if not cookie_headers:
        cookie = headers.get("Set-Cookie", "")
        cookie_headers = [cookie] if cookie else []
    for cookie_header in cookie_headers:
        cookie = _extract_sid_cookie(cookie_header)
        if cookie:
            return cookie
    return None


def _encode_multipart(
    fields: Mapping[str, Any],
    files: Sequence[Union[str, os.PathLike[str]]],
) -> Tuple[bytes, str]:
    boundary = f"----NexusQBittorrent{secrets.token_hex(16)}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        if value is None:
            continue
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                _stringify(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for file_path in files:
        path = Path(file_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/x-bittorrent"
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="torrents"; filename="{path.name}"\r\n'
                    f"Content-Type: {mime_type}\r\n\r\n"
                ).encode("utf-8"),
                path.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


_default_client: Optional[QBittorrentClient] = None
_default_client_key: Optional[tuple[str, str, str, str, str]] = None


def get_client() -> QBittorrentClient:
    """Get or create the default qBittorrent client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("QBITTORRENT_URL") or ""
    username = get_setting("QBITTORRENT_USERNAME") or ""
    password = get_setting("QBITTORRENT_PASSWORD") or ""
    timeout = get_setting("QBITTORRENT_TIMEOUT_S") or "30.0"
    api_path = get_setting("QBITTORRENT_API_PATH") or "/api/v2"
    key = (base_url, username, password, timeout, api_path)
    if _default_client is None or _default_client_key != key:
        _default_client = QBittorrentClient(
            base_url=base_url,
            username=username,
            password=password,
            timeout_s=float(timeout),
            api_path=api_path,
        )
        _default_client_key = key
    return _default_client
