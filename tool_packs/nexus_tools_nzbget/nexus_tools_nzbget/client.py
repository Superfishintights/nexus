"""Shared NZBGet JSON-RPC client for all NZBGet tools."""

from __future__ import annotations

import base64
import itertools
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)


class NZBGetRPCError(Exception):
    """Raised when NZBGet returns a JSON-RPC error object."""

    def __init__(self, method: str, error: Any):
        self.method = method
        self.error = error
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message") or "NZBGet JSON-RPC error"
            super().__init__(f"{message} (method={method}, code={code})")
        else:
            super().__init__(f"NZBGet JSON-RPC error in {method}: {error!r}")


class NZBGetClient:
    """Simple NZBGet JSON-RPC client using only standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        timeout_s: float = 30.0,
        rpc_path: str = "/jsonrpc",
    ):
        self.base_url = base_url or get_setting("NZBGET_URL")
        self.username = username if username is not None else get_setting("NZBGET_USERNAME")
        self.password = password if password is not None else get_setting("NZBGET_PASSWORD")
        self.timeout_s = timeout_s
        self.rpc_path = rpc_path or "/jsonrpc"
        self._ids = itertools.count(1)

        if not self.base_url:
            raise ValueError(
                "NZBGET_URL is required (set env var or put it in a `.env` file)."
            )
        if bool(self.username) != bool(self.password):
            raise ValueError(
                "Set both NZBGET_USERNAME and NZBGET_PASSWORD, or neither if NZBGet auth is disabled."
            )

        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"http://{self.base_url}"
        self.base_url = self.base_url.rstrip("/")

    @property
    def rpc_url(self) -> str:
        """Return the JSON-RPC endpoint URL."""
        parsed = urllib.parse.urlparse(self.base_url)
        if parsed.path.rstrip("/").endswith("/jsonrpc"):
            return self.base_url
        return f"{self.base_url}/{self.rpc_path.strip('/')}"

    def call(self, method: str, params: Optional[list[Any]] = None) -> Any:
        """Call an NZBGet JSON-RPC method with positional parameters."""
        request_id = next(self._ids)
        payload = {
            "method": method,
            "params": list(params or []),
            "id": request_id,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if self.username and self.password:
            token = f"{self.username}:{self.password}".encode("utf-8")
            headers["Authorization"] = "Basic " + base64.b64encode(token).decode("ascii")

        request = urllib.request.Request(
            self.rpc_url,
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw_data = response.read()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            details = f". Details: {error_body}" if error_body else ""
            raise Exception(f"HTTP {exc.code}: {exc.reason}{details}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}") from exc

        if not raw_data:
            return None

        try:
            payload = json.loads(raw_data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise Exception("Invalid JSON from NZBGet JSON-RPC API") from exc

        if not isinstance(payload, dict):
            raise Exception("Unexpected NZBGet JSON-RPC response shape")
        if payload.get("error") is not None:
            raise NZBGetRPCError(method, payload["error"])
        if payload.get("id") not in (request_id, None):
            raise Exception(
                f"Unexpected NZBGet JSON-RPC response id {payload.get('id')!r}; expected {request_id!r}"
            )
        return payload.get("result")


_default_client: Optional[NZBGetClient] = None
_default_client_key: Optional[tuple[str, str, str]] = None


def get_client() -> NZBGetClient:
    """Get or create the default NZBGet client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("NZBGET_URL")
    username = get_setting("NZBGET_USERNAME") or ""
    password = get_setting("NZBGET_PASSWORD") or ""
    if not base_url:
        _default_client = None
        _default_client_key = None
        return NZBGetClient(base_url=base_url, username=username, password=password)

    new_key = (base_url, username, password)
    if _default_client is None or _default_client_key != new_key:
        _default_client = NZBGetClient(
            base_url=base_url,
            username=username,
            password=password,
        )
        _default_client_key = new_key
    return _default_client
