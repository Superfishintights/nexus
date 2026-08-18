"""Shared Portainer HTTP client."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, Optional, Union

from nexus.config import get_setting

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 NexusMCP/0.1"
)
MEDIA_SEARCH_TERMS = ("plex", "tautulli", "sonarr", "radarr", "prowlarr", "sabnzbd", "qbittorrent")


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


def _coerce_endpoint_id(endpoint_id: Union[int, str]) -> str:
    endpoint = str(endpoint_id).strip()
    if not endpoint:
        raise ValueError("endpoint_id is required")
    return urllib.parse.quote(endpoint, safe="")


def _coerce_container_id(container_id: str) -> str:
    container = str(container_id).strip()
    if not container:
        raise ValueError("container_id is required")
    return urllib.parse.quote(container, safe="")


def _jsonable_container_summary(container: Dict[str, Any]) -> Dict[str, Any]:
    names = container.get("Names") or []
    if isinstance(names, str):
        names = [names]
    clean_names = [str(name).lstrip("/") for name in names if name]
    return {
        "id": container.get("Id"),
        "names": clean_names,
        "image": container.get("Image"),
        "image_id": container.get("ImageID"),
        "command": container.get("Command"),
        "created": container.get("Created"),
        "state": container.get("State"),
        "status": container.get("Status"),
        "ports": container.get("Ports") or [],
        "labels": container.get("Labels") or {},
    }


def _matches_terms(container: Dict[str, Any], terms: Iterable[str]) -> bool:
    haystack_parts = [
        container.get("Id"),
        container.get("id"),
        container.get("Image"),
        container.get("image"),
        container.get("ImageID"),
        container.get("image_id"),
        container.get("Command"),
        container.get("command"),
        container.get("State"),
        container.get("state"),
        container.get("Status"),
        container.get("status"),
    ]
    haystack_parts.extend(container.get("Names") or [])
    haystack_parts.extend(container.get("names") or [])
    labels = container.get("Labels") or {}
    if not labels:
        labels = container.get("labels") or {}
    if isinstance(labels, dict):
        for key, value in labels.items():
            haystack_parts.append(key)
            haystack_parts.append(value)
    haystack = " ".join(str(part).lower() for part in haystack_parts if part is not None)
    return all(term.lower() in haystack for term in terms if term)


class PortainerClient:
    """Portainer API client using only the standard library."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt: Optional[str] = None,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout_s: Optional[float] = None,
        api_path: str = "/api",
    ):
        self.base_url = _normalize_base_url(base_url or get_setting("PORTAINER_URL"))
        self.api_key = api_key or get_setting("PORTAINER_API_KEY")
        self.jwt = jwt or get_setting("PORTAINER_JWT", "PORTAINER_TOKEN")
        self.username = username or get_setting("PORTAINER_USERNAME")
        self.password = password or get_setting("PORTAINER_PASSWORD")
        self.timeout_s = timeout_s if timeout_s is not None else _float_setting("PORTAINER_TIMEOUT_S", 30.0)
        self.api_path = api_path

        if not self.base_url:
            raise ValueError("PORTAINER_URL is required (set env var or put it in a `.env` file).")
        if not (self.api_key or self.jwt or (self.username and self.password)):
            raise ValueError(
                "PORTAINER_API_KEY, PORTAINER_JWT/PORTAINER_TOKEN, or "
                "PORTAINER_USERNAME plus PORTAINER_PASSWORD is required."
            )

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request("GET", endpoint, params=params, api_path=api_path)

    def post(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
    ) -> Any:
        return self._request("POST", endpoint, params=params, body=body, api_path=api_path)

    def put(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
    ) -> Any:
        return self._request("PUT", endpoint, params=params, body=body, api_path=api_path)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, *, api_path: Optional[str] = None) -> Any:
        return self._request("DELETE", endpoint, params=params, api_path=api_path)

    def docker_proxy(
        self,
        method: str,
        endpoint_id: Union[int, str],
        docker_path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
    ) -> Any:
        path = docker_path.lstrip("/")
        endpoint = _coerce_endpoint_id(endpoint_id)
        return self._request(method, f"endpoints/{endpoint}/docker/{path}", params=params, body=body)

    def health(self) -> Dict[str, Any]:
        status = self.get("status")
        return status if isinstance(status, dict) else {"status": status}

    def system_status(self) -> Dict[str, Any]:
        status = self.get("system/status")
        return status if isinstance(status, dict) else {"status": status}

    def system_version(self) -> Dict[str, Any]:
        version = self.get("system/version")
        return version if isinstance(version, dict) else {"version": version}

    def list_environments(self, *, group_id: Optional[int] = None, tag_ids: Optional[list[int]] = None) -> list[Dict[str, Any]]:
        params: Dict[str, Any] = {"groupIds": group_id, "tagIds": tag_ids}
        payload = self.get("endpoints", params=params)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            environments = payload.get("endpoints") or payload.get("data") or []
            if isinstance(environments, list):
                return [item for item in environments if isinstance(item, dict)]
        return []

    def inspect_environment(self, endpoint_id: Union[int, str]) -> Dict[str, Any]:
        payload = self.get(f"endpoints/{_coerce_endpoint_id(endpoint_id)}")
        return payload if isinstance(payload, dict) else {"data": payload}

    def list_containers(
        self,
        endpoint_id: Union[int, str],
        *,
        all_containers: bool = True,
        search: Optional[str] = None,
        media_only: bool = False,
    ) -> list[Dict[str, Any]]:
        filters: Dict[str, Any] = {}
        params: Dict[str, Any] = {"all": all_containers}
        payload = self.docker_proxy("GET", endpoint_id, "containers/json", params=params)
        containers = payload if isinstance(payload, list) else []

        terms: list[str] = []
        if search:
            terms.extend(search.split())
        if media_only:
            filters["media_terms"] = list(MEDIA_SEARCH_TERMS)

        summaries = [_jsonable_container_summary(item) for item in containers if isinstance(item, dict)]
        if terms:
            summaries = [item for item in summaries if _matches_terms(item, terms)]
        if media_only:
            summaries = [item for item in summaries if any(_matches_terms(item, [term]) for term in MEDIA_SEARCH_TERMS)]
        return summaries

    def inspect_container(self, endpoint_id: Union[int, str], container_id: str) -> Dict[str, Any]:
        payload = self.docker_proxy("GET", endpoint_id, f"containers/{_coerce_container_id(container_id)}/json")
        return payload if isinstance(payload, dict) else {"data": payload}

    def container_status(self, endpoint_id: Union[int, str], container_id: str) -> Dict[str, Any]:
        container = self.inspect_container(endpoint_id, container_id)
        state = container.get("State") if isinstance(container.get("State"), dict) else {}
        config = container.get("Config") if isinstance(container.get("Config"), dict) else {}
        names = []
        if container.get("Name"):
            names.append(str(container.get("Name")).lstrip("/"))
        return {
            "id": container.get("Id") or container_id,
            "name": names[0] if names else None,
            "image": config.get("Image") or container.get("Image"),
            "state": state,
            "running": state.get("Running"),
            "status": state.get("Status"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "exit_code": state.get("ExitCode"),
        }

    def resolve_container(self, endpoint_id: Union[int, str], name: str, *, media_only: bool = False) -> Dict[str, Any]:
        needle = name.strip().lower()
        if not needle:
            raise ValueError("name is required")
        matches: list[Dict[str, Any]] = []
        for container in self.list_containers(endpoint_id, all_containers=True, media_only=media_only):
            names = [str(item).lower() for item in container.get("names") or []]
            container_id = str(container.get("id") or "").lower()
            if needle == container_id or container_id.startswith(needle) or needle in names:
                matches.append(container)
        if not matches:
            for container in self.list_containers(endpoint_id, all_containers=True, search=name, media_only=media_only):
                matches.append(container)
        unique = {str(item.get("id")): item for item in matches if item.get("id")}
        if not unique:
            raise ValueError(f"No Portainer container matched {name!r} on endpoint {endpoint_id}.")
        if len(unique) > 1:
            names = [", ".join(item.get("names") or []) or str(item.get("id")) for item in unique.values()]
            raise ValueError(f"Container name {name!r} matched multiple containers: {names}")
        return next(iter(unique.values()))

    def control_container(
        self,
        action: str,
        endpoint_id: Union[int, str],
        container_id: str,
        *,
        timeout_s: Optional[int] = None,
    ) -> Dict[str, Any]:
        if action not in {"start", "stop", "restart"}:
            raise ValueError("action must be one of: start, stop, restart")
        params = {"t": timeout_s} if timeout_s is not None and action in {"stop", "restart"} else None
        result = self.docker_proxy(
            "POST",
            endpoint_id,
            f"containers/{_coerce_container_id(container_id)}/{action}",
            params=params,
        )
        return {
            "endpoint_id": endpoint_id,
            "container_id": container_id,
            "action": action,
            "result": result,
        }

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
            if isinstance(value, bool):
                encoded[key] = "true" if value else "false"
            elif isinstance(value, (list, tuple)):
                values = [str(item) for item in value if item is not None]
                if values:
                    encoded[key] = values
            else:
                encoded[key] = str(value)
        return urllib.parse.urlencode(encoded, doseq=True)

    def _auth_headers(self) -> Dict[str, str]:
        if self.api_key:
            return {"X-API-KEY": self.api_key}
        token = self.jwt or self._login()
        return {"Authorization": f"Bearer {token}"}

    def _login(self) -> str:
        if self.jwt:
            return self.jwt
        if not (self.username and self.password):
            raise ValueError("PORTAINER_USERNAME and PORTAINER_PASSWORD are required to request a JWT.")
        payload = self._request(
            "POST",
            "auth",
            body={"Username": self.username, "Password": self.password},
            skip_auth=True,
        )
        if not isinstance(payload, dict) or not payload.get("jwt"):
            raise Exception("Portainer auth response did not include a JWT.")
        self.jwt = str(payload["jwt"])
        return self.jwt

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        api_path: Optional[str] = None,
        *,
        skip_auth: bool = False,
    ) -> Any:
        url = self._build_url(endpoint, api_path)
        query = self._encode_params(params)
        if query:
            url = f"{url}?{query}"

        headers = {
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if not skip_auth:
            headers.update(self._auth_headers())

        data = json.dumps(body).encode("utf-8") if body is not None else None
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw_data = response.read()
                if not raw_data:
                    return None
                response_data = raw_data.decode(response.headers.get_content_charset() or "utf-8")
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
            error_body = exc.read().decode("utf-8") if exc.fp else "No error details"
            raise Exception(f"HTTP {exc.code}: {exc.reason}. Details: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise Exception(f"URL Error: {exc.reason}") from exc
        except Exception as exc:
            raise Exception(f"Request failed: {str(exc)}") from exc


_default_client: Optional[PortainerClient] = None
_default_client_key: Optional[tuple[str, str, str, str, str]] = None


def get_client() -> PortainerClient:
    """Get or create the default Portainer client instance."""
    global _default_client, _default_client_key
    base_url = get_setting("PORTAINER_URL") or ""
    api_key = get_setting("PORTAINER_API_KEY") or ""
    jwt = get_setting("PORTAINER_JWT", "PORTAINER_TOKEN") or ""
    username = get_setting("PORTAINER_USERNAME") or ""
    password = get_setting("PORTAINER_PASSWORD") or ""
    new_key = (base_url, api_key, jwt, username, password)
    if _default_client is None or _default_client_key != new_key:
        _default_client = PortainerClient(
            base_url=base_url,
            api_key=api_key,
            jwt=jwt,
            username=username,
            password=password,
        )
        _default_client_key = new_key
    return _default_client
