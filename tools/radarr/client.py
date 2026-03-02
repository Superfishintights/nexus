"""Shared radarr HTTP client."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

from nexus.config import get_setting


class RadarrClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None, *, timeout_s: float = 30.0, api_path: str = '/api/v1'):
        self.base_url = base_url or get_setting('RADARR_URL')
        self.token = token or get_setting('RADARR_TOKEN')
        self.timeout_s = timeout_s
        self.api_path = api_path
        if not self.base_url:
            raise ValueError('RADARR_URL is required')
        if not self.token:
            raise ValueError('RADARR_TOKEN is required')
        if not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f'https://{self.base_url}'
        self.base_url = self.base_url.rstrip('/')

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request('GET', endpoint, params=params, api_path=api_path)

    def post(self, endpoint: str, body: Optional[Any] = None, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request('POST', endpoint, params=params, body=body, api_path=api_path)

    def put(self, endpoint: str, body: Optional[Any] = None, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request('PUT', endpoint, params=params, body=body, api_path=api_path)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request('DELETE', endpoint, params=params, api_path=api_path)

    def head(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request('HEAD', endpoint, params=params, api_path=api_path)

    def _build_url(self, endpoint: str, api_path: Optional[str]) -> str:
        endpoint = endpoint.lstrip('/')
        chosen_api_path = self.api_path if api_path is None else api_path
        path_prefix = chosen_api_path.strip('/') if chosen_api_path else ''
        url = self.base_url
        if path_prefix:
            url = f'{url}/{path_prefix}'
        if endpoint:
            url = f'{url}/{endpoint}'
        return url

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, body: Optional[Any] = None, api_path: Optional[str] = None) -> Any:
        url = self._build_url(endpoint, api_path)
        if params:
            q: Dict[str, Union[str, list[str]]] = {}
            for k, v in params.items():
                if v is None:
                    continue
                if isinstance(v, (list, tuple)):
                    values = [str(x) for x in v if x is not None]
                    if values:
                        q[k] = values
                else:
                    q[k] = str(v)
            if q:
                url += '?' + urllib.parse.urlencode(q, doseq=True)

        headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        data = None if body is None else json.dumps(body).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read()
                if not raw:
                    return None
                text = raw.decode(resp.headers.get_content_charset() or 'utf-8')
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8') if exc.fp else 'No error details'
            raise Exception(f'HTTP {exc.code}: {exc.reason}. Details: {detail}') from exc
        except urllib.error.URLError as exc:
            raise Exception(f'URL Error: {exc.reason}') from exc


_default_client: Optional[RadarrClient] = None
_default_client_key: Optional[tuple[str, str]] = None


def get_client() -> RadarrClient:
    global _default_client, _default_client_key
    base_url = get_setting('RADARR_URL')
    token = get_setting('RADARR_TOKEN')
    if not base_url or not token:
        _default_client = None
        _default_client_key = None
        return RadarrClient(base_url=base_url, token=token)
    key = (base_url, token)
    if _default_client is None or _default_client_key != key:
        _default_client = RadarrClient(base_url=base_url, token=token)
        _default_client_key = key
    return _default_client
