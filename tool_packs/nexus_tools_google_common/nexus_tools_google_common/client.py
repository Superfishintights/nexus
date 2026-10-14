"""Shared Google OAuth and API client for Nexus Google tool packs."""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import http.server
import json
import mimetypes
import os
import pathlib
import secrets
import socketserver
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from nexus.config import get_setting

_DEFAULT_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_DEFAULT_TOKEN_URL = "https://oauth2.googleapis.com/token"
_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_RETRY_COUNT = 2
_DEFAULT_RETRY_BASE_SECONDS = 0.5
_DEFAULT_TOKEN_FILE = "~/.config/nexus/google-token.json"
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS"}


class GoogleAuthError(RuntimeError):
    """Raised when Google credentials are missing, invalid, or cannot refresh."""


class GoogleApiError(RuntimeError):
    """Normalized Google API request failure."""

    def __init__(
        self,
        message: str,
        *,
        service: str,
        method: str,
        path: str,
        status: Optional[int] = None,
        reason: Optional[str] = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.service = service
        self.method = method
        self.path = path
        self.status = status
        self.reason = reason
        self.details = details


@dataclasses.dataclass(frozen=True)
class GoogleResponse:
    """Response wrapper used when callers need status or headers."""

    status: int
    headers: Dict[str, str]
    body: Any


class _LoopbackServer(socketserver.TCPServer):
    allow_reuse_address = True


class GoogleApiClient:
    """Small standard-library Google API client shared by app-specific packs."""

    SERVICE_BASE_URLS: Dict[str, str] = {
        "calendar": "https://www.googleapis.com/calendar/v3",
        "gmail": "https://gmail.googleapis.com/gmail/v1",
        "drive": "https://www.googleapis.com/drive/v3",
        "drive_upload": "https://www.googleapis.com/upload/drive/v3",
        "docs": "https://docs.googleapis.com/v1",
        "sheets": "https://sheets.googleapis.com/v4",
        "slides": "https://slides.googleapis.com/v1",
        "people": "https://people.googleapis.com/v1",
        "tasks": "https://tasks.googleapis.com/tasks/v1",
        "forms": "https://forms.googleapis.com/v1",
        "script": "https://script.googleapis.com/v1",
    }

    DEFAULT_USER_AGENT = "NexusMCP/0.1 nexus-tools-google-common/0.1"

    def __init__(
        self,
        *,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        token_file: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        retry_count: Optional[int] = None,
        retry_base_seconds: Optional[float] = None,
    ) -> None:
        self.token_url = _oauth_config_value("token_uri", "GOOGLE_TOKEN_URL", token_url, _DEFAULT_TOKEN_URL)
        self.timeout_seconds = _float_setting("GOOGLE_TIMEOUT_SECONDS", timeout_seconds, _DEFAULT_TIMEOUT_SECONDS)
        self.retry_count = _int_setting("GOOGLE_RETRY_COUNT", retry_count, _DEFAULT_RETRY_COUNT)
        self.retry_base_seconds = _float_setting(
            "GOOGLE_RETRY_BASE_SECONDS",
            retry_base_seconds,
            _DEFAULT_RETRY_BASE_SECONDS,
        )
        self.token_file = _setting("GOOGLE_TOKEN_FILE", token_file, _DEFAULT_TOKEN_FILE)

        token_payload = _read_token_file(self.token_file)
        self.access_token = _setting("GOOGLE_ACCESS_TOKEN", access_token, token_payload.get("access_token"))
        self.refresh_token = _setting("GOOGLE_REFRESH_TOKEN", refresh_token, token_payload.get("refresh_token"))
        self.client_id = _oauth_config_value("client_id", "GOOGLE_CLIENT_ID", client_id, None)
        self.client_secret = _oauth_config_value("client_secret", "GOOGLE_CLIENT_SECRET", client_secret, None)
        self._access_token_expires_at = _coerce_expiry(token_payload.get("expires_at"))

    @staticmethod
    def _normalize_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, separators=(",", ":"))
        return str(value)

    @classmethod
    def _normalize_params(cls, params: Optional[Mapping[str, Any]]) -> Optional[Sequence[Tuple[str, str]]]:
        if not params:
            return None
        normalized: List[Tuple[str, str]] = []
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    if item is not None:
                        normalized.append((key, cls._normalize_value(item)))
            else:
                normalized.append((key, cls._normalize_value(value)))
        return normalized or None

    def request(
        self,
        service: str,
        path: str,
        *,
        method: str = "GET",
        params: Optional[Mapping[str, Any]] = None,
        payload: Optional[Any] = None,
        data: Optional[bytes | str] = None,
        headers: Optional[Mapping[str, str]] = None,
        content_type: Optional[str] = None,
        binary: bool = False,
        response_headers: bool = False,
        media_upload: Optional[bytes | str | pathlib.Path] = None,
        upload_mime_type: Optional[str] = None,
        multipart_metadata: Optional[Mapping[str, Any]] = None,
        resumable: bool = False,
        resumable_upload_url: Optional[str] = None,
        allow_refresh: bool = True,
    ) -> Any:
        method_name = method.upper()
        body, request_content_type = self._build_body(
            payload=payload,
            data=data,
            content_type=content_type,
            media_upload=media_upload,
            upload_mime_type=upload_mime_type,
            multipart_metadata=multipart_metadata,
        )
        url = resumable_upload_url or self._build_url(service, path, params)
        request_headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Accept": "application/json",
            "User-Agent": self.DEFAULT_USER_AGENT,
        }
        request_headers.update(dict(headers or {}))
        if request_content_type and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = request_content_type
        if resumable and media_upload is not None:
            media_bytes, media_type = _read_media_upload(media_upload, upload_mime_type)
            request_headers.setdefault("X-Upload-Content-Type", media_type)
            request_headers.setdefault("X-Upload-Content-Length", str(len(media_bytes)))

        return self._request_with_retries(
            url,
            method_name,
            body,
            request_headers,
            service=service,
            path=path,
            binary=binary,
            response_headers=response_headers,
            allow_refresh=allow_refresh,
        )

    def _build_url(self, service: str, path: str, params: Optional[Mapping[str, Any]]) -> str:
        normalized_service = service.strip().lower()
        if normalized_service not in self.SERVICE_BASE_URLS:
            raise ValueError(f"Unsupported Google service '{service}'.")
        normalized_path = str(path).strip("/")
        url = self.SERVICE_BASE_URLS[normalized_service]
        if normalized_path:
            url = f"{url}/{normalized_path}"
        query_items = self._normalize_params(params)
        if query_items:
            url = f"{url}?{urllib.parse.urlencode(query_items, doseq=True)}"
        return url

    def _build_body(
        self,
        *,
        payload: Optional[Any],
        data: Optional[bytes | str],
        content_type: Optional[str],
        media_upload: Optional[bytes | str | pathlib.Path],
        upload_mime_type: Optional[str],
        multipart_metadata: Optional[Mapping[str, Any]],
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if multipart_metadata is not None:
            if media_upload is None:
                raise ValueError("multipart_metadata requires media_upload")
            media_bytes, media_type = _read_media_upload(media_upload, upload_mime_type)
            boundary = f"nexus-google-{secrets.token_hex(12)}"
            metadata = json.dumps(multipart_metadata, separators=(",", ":")).encode("utf-8")
            body = b"\r\n".join(
                [
                    f"--{boundary}".encode("ascii"),
                    b"Content-Type: application/json; charset=UTF-8",
                    b"",
                    metadata,
                    f"--{boundary}".encode("ascii"),
                    f"Content-Type: {media_type}".encode("ascii"),
                    b"",
                    media_bytes,
                    f"--{boundary}--".encode("ascii"),
                    b"",
                ]
            )
            return body, f'multipart/related; boundary="{boundary}"'
        if media_upload is not None:
            media_bytes, media_type = _read_media_upload(media_upload, upload_mime_type)
            return media_bytes, content_type or media_type
        if data is not None:
            if payload is not None:
                raise ValueError("Use either payload or data, not both")
            return _to_bytes(data), content_type or "application/octet-stream"
        if payload is None:
            return None, content_type
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload), content_type or "application/octet-stream"
        if isinstance(payload, str):
            return payload.encode("utf-8"), content_type or "text/plain; charset=UTF-8"
        return json.dumps(payload, separators=(",", ":")).encode("utf-8"), content_type or "application/json"

    def _request_with_retries(
        self,
        url: str,
        method: str,
        body: Optional[bytes],
        headers: Mapping[str, str],
        *,
        service: str,
        path: str,
        binary: bool,
        response_headers: bool,
        allow_refresh: bool,
    ) -> Any:
        attempts = max(0, self.retry_count) + 1
        refreshed = False
        for attempt in range(attempts):
            request = urllib.request.Request(url, data=body, method=method, headers=dict(headers))
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    decoded = self._decode_response(response, binary=binary)
                    if response_headers:
                        return GoogleResponse(response.status, dict(response.headers.items()), decoded)
                    return decoded
            except urllib.error.HTTPError as exc:
                details = _read_error_details(exc)
                if exc.code == 401 and allow_refresh and not refreshed:
                    refreshed = True
                    mutable_headers = dict(headers)
                    mutable_headers["Authorization"] = f"Bearer {self._refresh_access_token()}"
                    headers = mutable_headers
                    continue
                if exc.code in _RETRYABLE_STATUS and attempt < attempts - 1 and _retry_allowed(method, body):
                    _sleep_before_retry(exc, attempt, self.retry_base_seconds)
                    continue
                raise _api_error(exc, details, service=service, method=method, path=path) from exc
            except urllib.error.URLError as exc:
                if attempt < attempts - 1 and _retry_allowed(method, body):
                    time.sleep(self.retry_base_seconds * (2**attempt))
                    continue
                raise GoogleApiError(
                    f"Google API request failed ({service} {method} {path}): {exc.reason}",
                    service=service,
                    method=method,
                    path=path,
                    reason=str(exc.reason),
                ) from exc
        raise GoogleApiError("Google API request failed after retries", service=service, method=method, path=path)

    @staticmethod
    def _decode_response(response: urllib.request.addinfourl, *, binary: bool = False) -> Any:
        content = response.read()
        if binary:
            return content
        if response.status in {204, 205} or not content:
            return {}
        raw_text = content.decode("utf-8", errors="replace")
        content_type = (response.getheader("Content-Type") or "").lower()
        if "application/json" not in content_type:
            return {"contentType": content_type, "text": raw_text}
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {"contentType": content_type, "raw": raw_text, "status": response.status}

    def _get_access_token(self) -> str:
        if self.access_token and (self._access_token_expires_at is None or self._access_token_expires_at > time.time() + 60):
            return self.access_token
        if self.refresh_token:
            return self._refresh_access_token()
        raise GoogleAuthError(
            "Missing Google credentials. Set GOOGLE_ACCESS_TOKEN, configure GOOGLE_TOKEN_FILE, "
            "or provide GOOGLE_REFRESH_TOKEN with GOOGLE_CLIENT_ID."
        )

    def _refresh_access_token(self) -> str:
        if not (self.refresh_token and self.client_id):
            raise GoogleAuthError("Refresh token flow requires GOOGLE_REFRESH_TOKEN and GOOGLE_CLIENT_ID")
        payload = {
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        if self.client_secret:
            payload["client_secret"] = self.client_secret
        token_payload = _token_post(self.token_url, payload, timeout_seconds=self.timeout_seconds)
        access_token = token_payload.get("access_token")
        if not access_token:
            raise GoogleAuthError("Google token refresh response missing access_token")
        self.access_token = str(access_token)
        expires_in = token_payload.get("expires_in")
        self._access_token_expires_at = time.time() + float(expires_in) if isinstance(expires_in, (int, float)) else None
        if token_payload.get("refresh_token"):
            self.refresh_token = str(token_payload["refresh_token"])
        self._persist_token(token_payload)
        return self.access_token

    def _persist_token(self, token_payload: Mapping[str, Any]) -> None:
        if not self.token_file:
            return
        data = _read_token_file(self.token_file, missing_ok=True)
        data.update({key: value for key, value in token_payload.items() if key in {"access_token", "refresh_token", "scope", "token_type"}})
        if self.refresh_token and "refresh_token" not in data:
            data["refresh_token"] = self.refresh_token
        if self._access_token_expires_at:
            data["expires_at"] = self._access_token_expires_at
        _write_token_file(self.token_file, data)


def build_authorization_url(
    *,
    scopes: Sequence[str] | str | None = None,
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    access_type: str = "offline",
    prompt: str = "consent",
) -> Dict[str, str]:
    """Build a Google OAuth authorization URL using PKCE."""

    client_id = _oauth_config_value("client_id", "GOOGLE_CLIENT_ID", None, None)
    if not client_id:
        raise GoogleAuthError("GOOGLE_CLIENT_ID is required to build a Google authorization URL")
    code_verifier = _pkce_verifier()
    code_challenge = _pkce_challenge(code_verifier)
    redirect = redirect_uri or _redirect_uri_from_config("http://127.0.0.1:0/oauth2callback")
    oauth_state = state or secrets.token_urlsafe(24)
    query = {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": _normalize_scopes(scopes),
        "access_type": access_type,
        "prompt": prompt,
        "state": oauth_state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = _oauth_config_value("auth_uri", "GOOGLE_AUTH_URL", None, _DEFAULT_AUTH_URL)
    return {
        "url": f"{auth_url}?{urllib.parse.urlencode(query)}",
        "code_verifier": code_verifier,
        "state": oauth_state,
        "redirect_uri": redirect,
    }


def exchange_authorization_code(
    code: str,
    *,
    code_verifier: str,
    redirect_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """Exchange an OAuth authorization code for tokens and persist them."""

    client_id = _oauth_config_value("client_id", "GOOGLE_CLIENT_ID", None, None)
    if not client_id:
        raise GoogleAuthError("GOOGLE_CLIENT_ID is required to exchange a Google authorization code")
    payload = {
        "client_id": client_id,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri or _redirect_uri_from_config("http://127.0.0.1/oauth2callback"),
    }
    client_secret = _oauth_config_value("client_secret", "GOOGLE_CLIENT_SECRET", None, None)
    if client_secret:
        payload["client_secret"] = client_secret
    token_payload = _token_post(_oauth_config_value("token_uri", "GOOGLE_TOKEN_URL", None, _DEFAULT_TOKEN_URL), payload)
    if "expires_in" in token_payload:
        token_payload["expires_at"] = time.time() + float(token_payload["expires_in"])
    _write_token_file(_setting("GOOGLE_TOKEN_FILE", None, _DEFAULT_TOKEN_FILE), token_payload)
    return _sanitize_token_payload(token_payload)


def exchange_authorization_redirect(
    redirect_url: str,
    *,
    expected_state: str,
    code_verifier: str,
) -> Dict[str, Any]:
    """Validate a manual OAuth redirect and exchange its authorization code."""

    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)
    returned_state = (params.get("state") or [""])[0]
    if not secrets.compare_digest(returned_state, expected_state):
        raise GoogleAuthError("Google OAuth state mismatch")
    error = (params.get("error") or [""])[0]
    if error:
        raise GoogleAuthError(f"Google OAuth authorization failed: {error}")
    code = (params.get("code") or [""])[0]
    if not code:
        raise GoogleAuthError("Google OAuth redirect missing authorization code")
    redirect_uri = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return exchange_authorization_code(
        code,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri,
    )


def run_loopback_authorization(
    *,
    scopes: Sequence[str] | str | None = None,
    port: int = 0,
    open_browser: bool = False,
    timeout_seconds: int = 180,
) -> Dict[str, Any]:
    """Run a loopback OAuth flow bound to 127.0.0.1 and persist the resulting token."""

    captured: Dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if params.get("code"):
                captured["code"] = params["code"][0]
            if params.get("state"):
                captured["state"] = params["state"][0]
            body = b"Google authorization received. You may close this window."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    with _LoopbackServer(("127.0.0.1", port), Handler) as server:
        server.timeout = 1.0
        actual_port = int(server.server_address[1])
        redirect_uri = f"http://127.0.0.1:{actual_port}/oauth2callback"
        auth = build_authorization_url(scopes=scopes, redirect_uri=redirect_uri)
        if open_browser:
            webbrowser.open(auth["url"])
        deadline = time.time() + timeout_seconds
        while time.time() < deadline and "code" not in captured:
            server.handle_request()
        if "code" not in captured:
            raise GoogleAuthError("Timed out waiting for Google OAuth loopback callback")
        if captured.get("state") != auth["state"]:
            raise GoogleAuthError("Google OAuth state mismatch")
        return exchange_authorization_code(
            captured["code"],
            code_verifier=auth["code_verifier"],
            redirect_uri=redirect_uri,
        )


def get_client() -> GoogleApiClient:
    """Get or create the shared Google client instance for current settings."""

    global _default_client, _default_client_key
    key = tuple(
        _setting(name, None, None)
        for name in (
            "GOOGLE_ACCESS_TOKEN",
            "GOOGLE_REFRESH_TOKEN",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_CLIENT_CONFIG_FILE",
            "GOOGLE_TOKEN_URL",
            "GOOGLE_TOKEN_FILE",
            "GOOGLE_TIMEOUT_SECONDS",
            "GOOGLE_RETRY_COUNT",
            "GOOGLE_RETRY_BASE_SECONDS",
        )
    )
    if _default_client is None or _default_client_key != key:
        _default_client = GoogleApiClient()
        _default_client_key = key
    return _default_client


def quote_path_segment(value: Any, *, safe: str = "@") -> str:
    """URL-quote a single path segment."""

    return urllib.parse.quote(str(value), safe=safe)


def quote_resource_name(value: Any) -> str:
    """URL-quote an API resource name while preserving slashes."""

    return urllib.parse.quote(str(value).strip("/"), safe="/@")


def coerce_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Payload must be valid JSON") from exc
    return value


def coerce_list(value: Any) -> Optional[List[Any]]:
    parsed = coerce_json(value)
    if parsed is None:
        return None
    if isinstance(parsed, str):
        parsed = [parsed]
    if isinstance(parsed, tuple):
        parsed = list(parsed)
    if not isinstance(parsed, list):
        raise ValueError("Expected a JSON array")
    return [item for item in parsed]


def coerce_optional_str(value: Any, *, allow_empty: bool = False) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if (text or allow_empty) else None


def coerce_optional_int(value: Any, *, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def coerce_optional_bool(value: Any, *, default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on", "y"}:
        return True
    if text in {"false", "0", "no", "off", "n"}:
        return False
    return default


def _setting(name: str, explicit: Optional[Any], default: Optional[Any]) -> Optional[str]:
    if explicit is not None:
        value = str(explicit).strip()
        return value or None
    value = get_setting(name)
    if value is None:
        return str(default) if default is not None else None
    text = str(value).strip()
    return text or (str(default) if default is not None else None)


def _int_setting(name: str, explicit: Optional[int], default: int) -> int:
    try:
        return int(explicit if explicit is not None else (get_setting(name) or default))
    except (TypeError, ValueError):
        return default


def _float_setting(name: str, explicit: Optional[float], default: float) -> float:
    try:
        return float(explicit if explicit is not None else (get_setting(name) or default))
    except (TypeError, ValueError):
        return default


def _oauth_config_value(
    config_key: str,
    env_name: str,
    explicit: Optional[Any],
    default: Optional[Any],
) -> Optional[str]:
    value = _setting(env_name, explicit, None)
    if value:
        return value
    config = _read_client_config()
    config_value = config.get(config_key)
    if config_value:
        return str(config_value).strip() or None
    return str(default) if default is not None else None


def _redirect_uri_from_config(default: str) -> str:
    value = _setting("GOOGLE_REDIRECT_URI", None, None)
    if value:
        return value
    redirect_uris = _read_client_config().get("redirect_uris")
    if isinstance(redirect_uris, list):
        for item in redirect_uris:
            text = str(item).strip()
            if text:
                return text
    return default


def _read_client_config() -> Dict[str, Any]:
    path = _setting("GOOGLE_CLIENT_CONFIG_FILE", None, None)
    if not path:
        return {}
    data = _read_secure_json_file(path, description="Google client config")
    installed = data.get("installed")
    if not isinstance(installed, dict):
        raise GoogleAuthError("Google client config file must contain an installed object")
    return installed


def _token_path(path: Optional[str]) -> Optional[pathlib.Path]:
    if not path:
        return None
    return pathlib.Path(path).expanduser()


def _read_token_file(path: Optional[str], *, missing_ok: bool = True) -> Dict[str, Any]:
    token_path = _token_path(path)
    if token_path is None or not token_path.exists():
        if missing_ok:
            return {}
        raise GoogleAuthError(f"Google token file does not exist: {token_path}")
    return _read_secure_json_file(str(token_path), description="Google token file")


def _read_secure_json_file(path: str, *, description: str) -> Dict[str, Any]:
    file_path = pathlib.Path(path).expanduser()
    try:
        mode = file_path.stat().st_mode & 0o777
    except OSError as exc:
        raise GoogleAuthError(f"Could not read {description}: {file_path}") from exc
    if mode & 0o077:
        raise GoogleAuthError(f"{description} permissions must be 0600: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise GoogleAuthError(f"Could not read {description}: {file_path}") from exc
    if not isinstance(data, dict):
        raise GoogleAuthError(f"{description} must contain a JSON object: {file_path}")
    return data


def _write_token_file(path: Optional[str], data: Mapping[str, Any]) -> None:
    token_path = _token_path(path)
    if token_path is None:
        return
    token_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(token_path.parent, 0o700)
    except OSError:
        pass
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(token_path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(dict(data), handle, sort_keys=True)
            handle.write("\n")
    finally:
        try:
            os.chmod(token_path, 0o600)
        except OSError:
            pass


def _coerce_expiry(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _token_post(url: str, payload: Mapping[str, Any], *, timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode({key: value for key, value in payload.items() if value is not None}).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": GoogleApiClient.DEFAULT_USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = _read_error_details(exc)
        message = _error_message(details) or f"HTTP {exc.code} {exc.reason}"
        raise GoogleAuthError(f"Google token request failed: {message}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise GoogleAuthError(f"Google token request failed: {exc}") from exc
    if not isinstance(data, dict):
        raise GoogleAuthError("Google token response must be a JSON object")
    return data


def _read_media_upload(media: bytes | str | pathlib.Path, mime_type: Optional[str]) -> Tuple[bytes, str]:
    if isinstance(media, bytes):
        return media, mime_type or "application/octet-stream"
    path = pathlib.Path(media).expanduser()
    if path.exists() and path.is_file():
        detected = mime_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        return path.read_bytes(), detected
    return str(media).encode("utf-8"), mime_type or "text/plain; charset=UTF-8"


def _to_bytes(value: bytes | str) -> bytes:
    return value if isinstance(value, bytes) else value.encode("utf-8")


def _read_error_details(exc: urllib.error.HTTPError) -> Any:
    raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _error_message(details: Any) -> Optional[str]:
    if isinstance(details, dict):
        error = details.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("status") or "").strip() or None
        if isinstance(error, str):
            return error
    if isinstance(details, str):
        return details
    return None


def _api_error(
    exc: urllib.error.HTTPError,
    details: Any,
    *,
    service: str,
    method: str,
    path: str,
) -> GoogleApiError:
    message = _error_message(details) or f"HTTP {exc.code} {exc.reason}"
    return GoogleApiError(
        f"Google API request failed ({service} {method} {path}): {message}",
        service=service,
        method=method,
        path=path,
        status=exc.code,
        reason=exc.reason,
        details=details,
    )


def _retry_allowed(method: str, body: Optional[bytes]) -> bool:
    del body
    return method in _IDEMPOTENT_METHODS


def _sleep_before_retry(exc: urllib.error.HTTPError, attempt: int, base_seconds: float) -> None:
    retry_after = exc.headers.get("Retry-After") if exc.headers else None
    if retry_after:
        try:
            time.sleep(min(float(retry_after), 30.0))
            return
        except ValueError:
            pass
    time.sleep(base_seconds * (2**attempt))


def _pkce_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _normalize_scopes(scopes: Sequence[str] | str | None) -> str:
    if scopes is None:
        raw = _setting("GOOGLE_SCOPES", None, "")
        if raw:
            scopes = raw
        else:
            return "openid email profile"
    if isinstance(scopes, str):
        return " ".join(item for item in scopes.replace(",", " ").split() if item)
    return " ".join(str(item).strip() for item in scopes if str(item).strip())


def _sanitize_token_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"access_token", "refresh_token", "id_token"}
    }


_default_client: Optional[GoogleApiClient] = None
_default_client_key: Optional[Tuple[Optional[str], ...]] = None
