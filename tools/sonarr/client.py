"""Shared Sonarr HTTP client for all Sonarr tools."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

from nexus.config import get_setting


class SonarrClient:
    """Simple Sonarr API client using only standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        timeout_s: float = 30.0,
        api_path: str = "/api/v3",
    ):
        self.base_url = base_url or get_setting("SONARR_URL")
        self.api_key = api_key or get_setting("SONARR_API_KEY")
        self.timeout_s = timeout_s
        self.api_path = api_path

        if not self.base_url:
            raise ValueError(
                "SONARR_URL is required (set env var or put it in a `.env` file)."
            )
        if not self.api_key:
            raise ValueError(
                "SONARR_API_KEY is required (set env var or put it in a `.env` file)."
            )

        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"https://{self.base_url}"

        self.base_url = self.base_url.rstrip("/")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request to Sonarr API."""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a POST request to Sonarr API."""
        return self._request("POST", endpoint, params=params, body=body)

    def put(self, endpoint: str, body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a PUT request to Sonarr API."""
        return self._request("PUT", endpoint, params=params, body=body)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a DELETE request to Sonarr API."""
        return self._request("DELETE", endpoint, params=params)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}{self.api_path}/{endpoint}"

        if params:
            # Filter None values and convert bools/ints
            query_params = {}
            for k, v in params.items():
                if v is None:
                    continue
                if isinstance(v, bool):
                    query_params[k] = "true" if v else "false"
                else:
                    query_params[k] = str(v)
            if query_params:
                url += f"?{urllib.parse.urlencode(query_params)}"

        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                response_data = response.read().decode("utf-8")
                if not response_data:
                    return None
                return json.loads(response_data)

        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}") from exc


_default_client: Optional[SonarrClient] = None
_default_client_key: Optional[tuple[str, str]] = None


def get_client() -> SonarrClient:
    """Get or create the default Sonarr client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("SONARR_URL")
    api_key = get_setting("SONARR_API_KEY")
    if not base_url or not api_key:
        _default_client = None
        _default_client_key = None
        return SonarrClient(base_url=base_url, api_key=api_key)

    new_key = (base_url, api_key)
    if _default_client is None or _default_client_key != new_key:
        _default_client = SonarrClient(base_url=base_url, api_key=api_key)
        _default_client_key = new_key
    return _default_client
