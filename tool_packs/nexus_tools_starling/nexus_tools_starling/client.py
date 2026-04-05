"""Shared Starling HTTP client."""

from __future__ import annotations

import base64
import json
import shlex
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

from nexus.config import get_setting

from .errors import (
    StarlingAPIError,
    StarlingAuthError,
    StarlingMTLSError,
    StarlingScopeError,
    StarlingSigningError,
)
from .manifest import is_binary_response, is_text_response, requires_signature

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)
DEFAULT_PRODUCTION_BASE_URL = "https://api.starlingbank.com"
DEFAULT_SANDBOX_BASE_URL = "https://api-sandbox.starlingbank.com"


def _normalize_base_url(value: Optional[str]) -> str:
    base_url = (value or "").strip()
    if not base_url:
        return ""
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    return base_url.rstrip("/")


def _float_setting(name: str, default: float) -> float:
    raw = get_setting(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class StarlingClient:
    """Starling API client using the standard library only."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        timeout_s: Optional[float] = None,
        api_path: str = "/api/v2",
        signing_command: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
    ):
        env_name = (get_setting("STARLING_ENV") or "production").strip().lower()
        default_base_url = (
            DEFAULT_SANDBOX_BASE_URL if env_name.startswith("sandbox") else DEFAULT_PRODUCTION_BASE_URL
        )

        self.base_url = _normalize_base_url(
            base_url or get_setting("STARLING_API_BASE_URL", "STARLING_URL") or default_base_url
        )
        self.token = token or get_setting("STARLING_ACCESS_TOKEN", "STARLING_TOKEN")
        self.timeout_s = timeout_s if timeout_s is not None else _float_setting("STARLING_TIMEOUT_S", 30.0)
        self.api_path = api_path
        self.signing_command = signing_command or get_setting("STARLING_SIGNING_COMMAND")
        self.public_key_id = get_setting("STARLING_PUBLIC_KEY_ID")
        self.ssl_context = ssl_context or self._build_ssl_context()

        if not self.base_url:
            raise StarlingAuthError("STARLING_API_BASE_URL or STARLING_URL is required")
        if not self.token:
            raise StarlingAuthError("STARLING_ACCESS_TOKEN or STARLING_TOKEN is required")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return self._request("GET", endpoint, params=params, api_path=api_path, headers=headers)

    def post(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Any:
        return self._request(
            "POST",
            endpoint,
            params=params,
            body=body,
            api_path=api_path,
            headers=headers,
            content_type=content_type,
        )

    def put(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Any:
        return self._request(
            "PUT",
            endpoint,
            params=params,
            body=body,
            api_path=api_path,
            headers=headers,
            content_type=content_type,
        )

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return self._request("DELETE", endpoint, params=params, api_path=api_path, headers=headers)

    def head(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return self._request("HEAD", endpoint, params=params, api_path=api_path, headers=headers)

    def _build_ssl_context(self) -> ssl.SSLContext:
        ca_bundle_path = get_setting("STARLING_CA_BUNDLE_PATH")
        client_cert_path = get_setting("STARLING_CLIENT_CERT_PATH")
        client_key_path = get_setting("STARLING_CLIENT_KEY_PATH")

        try:
            context = ssl.create_default_context(cafile=ca_bundle_path or None)
            if client_cert_path and client_key_path:
                context.load_cert_chain(client_cert_path, client_key_path)
            return context
        except Exception as exc:  # pragma: no cover
            raise StarlingMTLSError(f"Unable to configure TLS context: {exc}") from exc

    def _build_url(self, endpoint: str, api_path: Optional[str]) -> str:
        endpoint = endpoint.lstrip("/")
        chosen_api_path = self.api_path if api_path is None else api_path
        path_prefix = chosen_api_path.strip("/") if chosen_api_path else ""
        url = self.base_url
        if path_prefix:
            url = f"{url}/{path_prefix}"
        if endpoint:
            url = f"{url}/{endpoint}"
        return url

    def _encode_params(self, params: Optional[Dict[str, Any]]) -> str:
        if not params:
            return ""

        encoded: Dict[str, Union[str, list[str]]] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                values = [str(item) for item in value if item is not None]
                if values:
                    encoded[key] = values
                continue
            encoded[key] = str(value)

        if not encoded:
            return ""
        return urllib.parse.urlencode(encoded, doseq=True)

    def _prepare_body(
        self, body: Optional[Any], content_type: Optional[str]
    ) -> tuple[Optional[bytes], Optional[str]]:
        if body is None:
            return None, content_type

        if isinstance(body, (bytes, bytearray)):
            return bytes(body), content_type or "application/octet-stream"

        if isinstance(body, str):
            return body.encode("utf-8"), content_type or "text/plain; charset=utf-8"

        if isinstance(body, dict):
            raw_base64 = body.get("content_base64") or body.get("raw_bytes_base64")
            if isinstance(raw_base64, str):
                return (
                    base64.b64decode(raw_base64.encode("ascii")),
                    body.get("content_type") or content_type or "application/octet-stream",
                )

        return json.dumps(body).encode("utf-8"), content_type or "application/json"

    def _build_signing_headers(
        self,
        *,
        method: str,
        url: str,
        endpoint: str,
        data: Optional[bytes],
        content_type: Optional[str],
    ) -> Dict[str, str]:
        if not self.signing_command:
            raise StarlingSigningError(
                "Signed Starling endpoint requires STARLING_SIGNING_COMMAND to return per-request headers."
            )

        signer_payload = {
            "method": method,
            "url": url,
            "endpoint": endpoint,
            "body_base64": base64.b64encode(data or b"").decode("ascii"),
            "content_type": content_type or "",
            "public_key_id": self.public_key_id,
        }

        try:
            completed = subprocess.run(
                shlex.split(self.signing_command),
                input=json.dumps(signer_payload).encode("utf-8"),
                capture_output=True,
                check=False,
                timeout=min(self.timeout_s, 15.0),
            )
        except Exception as exc:  # pragma: no cover
            raise StarlingSigningError(f"Failed to execute STARLING_SIGNING_COMMAND: {exc}") from exc

        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", errors="replace").strip()
            raise StarlingSigningError(
                f"STARLING_SIGNING_COMMAND exited with status {completed.returncode}: {stderr or 'no stderr'}"
            )

        stdout = completed.stdout.decode("utf-8", errors="replace").strip()
        if not stdout:
            raise StarlingSigningError("STARLING_SIGNING_COMMAND returned no output")

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise StarlingSigningError("STARLING_SIGNING_COMMAND must return JSON") from exc

        if isinstance(payload, dict) and isinstance(payload.get("headers"), dict):
            payload = payload["headers"]
        if not isinstance(payload, dict):
            raise StarlingSigningError("STARLING_SIGNING_COMMAND must return a JSON object of headers")

        headers: Dict[str, str] = {}
        for key, value in payload.items():
            headers[str(key)] = str(value)
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        api_path: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Any:
        url = self._build_url(endpoint, api_path)
        query = self._encode_params(params)
        if query:
            url = f"{url}?{query}"

        data, effective_content_type = self._prepare_body(body, content_type)
        request_headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if effective_content_type is not None:
            request_headers["Content-Type"] = effective_content_type
        if headers:
            request_headers.update(headers)

        if requires_signature(method, endpoint):
            request_headers.update(
                self._build_signing_headers(
                    method=method,
                    url=url,
                    endpoint=endpoint,
                    data=data,
                    content_type=effective_content_type,
                )
            )

        try:
            request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
            with urllib.request.urlopen(request, timeout=self.timeout_s, context=self.ssl_context) as response:
                raw = response.read()
                return self._decode_response(endpoint=endpoint, raw=raw, response=response)
        except urllib.error.HTTPError as exc:
            raw = exc.read() if exc.fp is not None else b""
            detail = self._decode_error_detail(endpoint=endpoint, raw=raw, response=exc)
            message = f"HTTP {exc.code}: {exc.reason}"
            if detail:
                message = f"{message}. Details: {detail}"

            if exc.code == 401:
                raise StarlingAuthError(message) from exc
            if exc.code == 403:
                raise StarlingScopeError(message) from exc
            raise StarlingAPIError(
                message,
                status_code=exc.code,
                detail=detail,
                method=method,
                endpoint=endpoint,
            ) from exc
        except urllib.error.URLError as exc:
            raise StarlingAPIError(
                f"URL Error: {exc.reason}",
                status_code=None,
                detail=str(exc.reason),
                method=method,
                endpoint=endpoint,
            ) from exc

    def _decode_response(
        self,
        *,
        endpoint: str,
        raw: bytes,
        response: Union[urllib.response.addinfourl, urllib.error.HTTPError],
    ) -> Any:
        if not raw:
            return None

        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"

        if is_binary_response(endpoint, content_type):
            return {
                "content_type": content_type,
                "content_length": len(raw),
                "content_base64": base64.b64encode(raw).decode("ascii"),
                "content_disposition": response.headers.get("Content-Disposition"),
            }

        if is_text_response(endpoint, content_type):
            text = raw.decode(charset, errors="replace")
            return {
                "content_type": content_type,
                "content_length": len(raw),
                "text": text,
                "content_base64": base64.b64encode(raw).decode("ascii"),
            }

        if "json" in content_type or raw[:1] in {b"{", b"["}:
            try:
                return json.loads(raw.decode(charset))
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass

        try:
            return raw.decode(charset)
        except UnicodeDecodeError:
            return {
                "content_type": content_type,
                "content_length": len(raw),
                "content_base64": base64.b64encode(raw).decode("ascii"),
            }

    def _decode_error_detail(
        self,
        *,
        endpoint: str,
        raw: bytes,
        response: Union[urllib.response.addinfourl, urllib.error.HTTPError],
    ) -> Any:
        decoded = self._decode_response(endpoint=endpoint, raw=raw, response=response)
        if isinstance(decoded, dict) and "text" in decoded:
            return decoded["text"]
        return decoded


_default_client: Optional[StarlingClient] = None
_default_client_key: Optional[tuple[str, str, str, str, str, str]] = None


def get_client() -> StarlingClient:
    global _default_client, _default_client_key

    base_url = _normalize_base_url(get_setting("STARLING_API_BASE_URL", "STARLING_URL"))
    token = get_setting("STARLING_ACCESS_TOKEN", "STARLING_TOKEN") or ""
    signing_command = get_setting("STARLING_SIGNING_COMMAND") or ""
    client_cert_path = get_setting("STARLING_CLIENT_CERT_PATH") or ""
    client_key_path = get_setting("STARLING_CLIENT_KEY_PATH") or ""
    ca_bundle_path = get_setting("STARLING_CA_BUNDLE_PATH") or ""
    key = (base_url, token, signing_command, client_cert_path, client_key_path, ca_bundle_path)

    if _default_client is None or _default_client_key != key:
        _default_client = StarlingClient(base_url=base_url or None, token=token or None)
        _default_client_key = key
    return _default_client
