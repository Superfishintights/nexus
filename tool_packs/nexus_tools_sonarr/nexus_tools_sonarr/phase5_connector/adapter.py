"""Sonarr adapter for the shared long-lived connector worker protocol."""

from __future__ import annotations

import http.client
import json
import threading
import time
import urllib.parse
from collections.abc import Mapping
from typing import Any

from ..client import DEFAULT_USER_AGENT
from .source import EXPECTED_SOURCE_REVISION_DIGEST, load_source


class SonarrConnectorError(RuntimeError):
    """Credential-safe connector failure."""


class PersistentSonarrClient:
    """One persistent HTTP/1.1 transport per connector Connection."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout_s: float = 30.0,
        api_path: str = "/api/v3",
        connection_factory: Any = None,
    ) -> None:
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Sonarr endpoint must be an HTTP(S) URL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.api_path = api_path
        self._parsed = parsed
        self._base_path = parsed.path.rstrip("/")
        self._connection_factory = connection_factory
        self._connection: Any = None
        self._lock = threading.Lock()
        self.connection_count = 0
        self.request_count = 0

    def get(self, endpoint: str, params: Any = None, *, api_path: str | None = None) -> Any:
        return self._request("GET", endpoint, params=params, api_path=api_path)

    def post(self, endpoint: str, body: Any = None, params: Any = None, *, api_path: str | None = None) -> Any:
        return self._request("POST", endpoint, params=params, body=body, api_path=api_path)

    def put(self, endpoint: str, body: Any = None, params: Any = None, *, api_path: str | None = None) -> Any:
        return self._request("PUT", endpoint, params=params, body=body, api_path=api_path)

    def delete(self, endpoint: str, params: Any = None, *, api_path: str | None = None) -> Any:
        return self._request("DELETE", endpoint, params=params, api_path=api_path)

    def head(self, endpoint: str, params: Any = None, *, api_path: str | None = None) -> Any:
        return self._request("HEAD", endpoint, params=params, api_path=api_path)

    def close(self) -> None:
        with self._lock:
            self._drop_connection()

    def _new_connection(self) -> Any:
        if self._connection_factory is not None:
            connection = self._connection_factory(self._parsed, self.timeout_s)
        else:
            factory = http.client.HTTPSConnection if self._parsed.scheme == "https" else http.client.HTTPConnection
            connection = factory(self._parsed.hostname, port=self._parsed.port, timeout=self.timeout_s)
        self.connection_count += 1
        return connection

    def _drop_connection(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None:
            connection.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Any = None,
        api_path: str | None = None,
    ) -> Any:
        path_parts = [self._base_path, (self.api_path if api_path is None else api_path).strip("/"), endpoint.strip("/")]
        path = "/" + "/".join(part for part in path_parts if part)
        if params:
            query: list[tuple[str, str]] = []
            for key, raw in params.items():
                values = raw if isinstance(raw, (list, tuple)) else [raw]
                for value in values:
                    if value is None:
                        continue
                    query.append((key, "true" if value is True else "false" if value is False else str(value)))
            if query:
                path += "?" + urllib.parse.urlencode(query)
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        with self._lock:
            if self._connection is None:
                self._connection = self._new_connection()
            try:
                self._connection.request(method, path, body=payload, headers=headers)
                response = self._connection.getresponse()
                raw = response.read()
                self.request_count += 1
                if response.status >= 400:
                    raise SonarrConnectorError(f"Sonarr upstream returned HTTP {response.status}")
                if getattr(response, "will_close", False):
                    self._drop_connection()
            except Exception:
                self._drop_connection()
                raise
        if not raw:
            return None
        text = raw.decode("utf-8")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text


class SonarrConnectorAdapter:
    """One reusable client for one worker-managed Sonarr Connection.

    The shared worker resolves Phase 3 SecretReference objects before calling
    ``create_connector``. This object receives only that connector-local copy;
    it has no secret provider, catalogue, policy, filesystem, or ambient fetch
    authority.
    """

    __slots__ = ("_connection_id", "_client", "_tools", "_aliases")

    def __init__(self, connection_id: str, client: Any) -> None:
        self._connection_id = connection_id
        self._client: Any | None = client
        source = load_source()
        self._tools = {
            item["identityMapping"]["legacyCanonicalName"]: item for item in source["tools"]
        }
        self._aliases = {
            alias: item["identityMapping"]["legacyCanonicalName"]
            for item in source["tools"]
            for alias in item["identityMapping"]["aliases"]
        }

    def __repr__(self) -> str:
        return f"SonarrConnectorAdapter(connection_id={self._connection_id!r}, closed={self._client is None})"

    def diagnostics(self) -> dict[str, Any]:
        return {
            "connectionId": self._connection_id,
            "integrationId": "integration.sonarr",
            "closed": self._client is None,
            "canonicalTools": len(self._tools),
            "aliases": len(self._aliases),
        }

    def resolve_name(self, operation: str) -> str:
        if operation in self._tools:
            return operation
        if operation in self._aliases:
            return self._aliases[operation]
        dot_name = f"sonarr.{operation.removeprefix('sonarr:')}"
        if dot_name in self._tools:
            return dot_name
        raise KeyError(operation)

    def describe(self, operation: str) -> Mapping[str, Any]:
        return self._tools[self.resolve_name(operation)]

    def invoke(
        self,
        operation: str,
        arguments: Mapping[str, Any],
        context: Any,
    ) -> Any:
        """Shared-worker Connector.invoke implementation for synchronous Sonarr calls."""
        deadline = getattr(context, "deadline_monotonic", None)
        if isinstance(deadline, (int, float)) and time.monotonic() >= deadline:
            raise TimeoutError("Sonarr invocation deadline elapsed")
        canonical = self.resolve_name(operation)
        args = dict(arguments)
        try:
            result = (
                self._list_season_releases(args)
                if canonical == "sonarr.list_season_releases"
                else self._invoke_rest(self._tools[canonical], args)
            )
            _assert_json_safe(result)
            return result
        except SonarrConnectorError:
            raise
        except (KeyError, TypeError, ValueError, TimeoutError):
            raise
        except Exception:
            raise SonarrConnectorError("Sonarr connector invocation failed") from None

    def close(self) -> None:
        client = self._client
        self._client = None
        close = getattr(client, "close", None)
        if close is not None:
            try:
                close()
            except Exception:
                raise SonarrConnectorError("Sonarr connector close failed") from None

    def _invoke_rest(self, item: Mapping[str, Any], arguments: dict[str, Any]) -> Any:
        client = self._require_client()
        schema = item["schemas"]["original"]["inputSchema"]
        allowed = set(schema["properties"])
        unknown = set(arguments) - allowed
        if unknown:
            raise TypeError(f"unexpected arguments: {sorted(unknown)}")
        for required in schema.get("required", ()):
            if required not in arguments:
                raise TypeError(f"missing required argument: {required}")
        transport = item["source"]["transport"]
        path_values = {key: value for key, value in arguments.items() if key not in {"params", "body"}}
        try:
            endpoint = transport["endpointTemplate"].format(**path_values)
        except KeyError as error:
            raise TypeError(f"missing required argument: {error.args[0]}") from None
        method = transport["method"].lower()
        kwargs: dict[str, Any] = {"params": arguments.get("params"), "api_path": transport["apiPath"]}
        if method in {"post", "put"}:
            kwargs["body"] = arguments.get("body")
        return getattr(client, method)(endpoint, **kwargs)

    def _list_season_releases(self, arguments: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "series_id", "series_title", "query", "season_number", "quality_contains",
            "full_season_only", "min_custom_format_score", "positive_score_only", "max_results",
            "include_rejected", "download_allowed",
        }
        unknown = set(arguments) - allowed
        if unknown:
            raise TypeError(f"unexpected arguments: {sorted(unknown)}")
        client = self._require_client()
        series_id = arguments.get("series_id")
        title = arguments.get("series_title") or arguments.get("query")
        if series_id is None:
            if not title:
                raise ValueError("Provide series_id or series_title/query")
            series = _choose_series(client.get("series"), str(title))
            if series is None:
                series = _choose_series(client.get("series/lookup", params={"term": title}), str(title))
            if series is None:
                raise ValueError("No Sonarr series found")
            series_id = series.get("id")
            title = series.get("title") or title
        series_id = _as_int(series_id, "series_id")
        season_number = _as_int(arguments.get("season_number"), "season_number")
        releases = client.get("release", params={"seriesId": series_id, "seasonNumber": season_number})
        if not isinstance(releases, list):
            releases = []
        minimum = arguments.get("min_custom_format_score")
        if arguments.get("positive_score_only", False) and minimum is None:
            minimum = 1
        quality = arguments.get("quality_contains")
        filtered = []
        for release in releases:
            if not isinstance(release, dict):
                continue
            if arguments.get("full_season_only", True) and release.get("fullSeason") is not True:
                continue
            if not arguments.get("include_rejected", False) and release.get("rejected") is True:
                continue
            download_allowed = arguments.get("download_allowed")
            if download_allowed is not None and release.get("downloadAllowed") is not download_allowed:
                continue
            if minimum is not None and _score(release) < int(minimum):
                continue
            if quality and quality.casefold() not in _quality_haystack(release):
                continue
            filtered.append(release)
        filtered.sort(key=lambda value: (_score(value), _integer(value.get("seeders"), -1)), reverse=True)
        limit = arguments.get("max_results", 50)
        returned = filtered if limit is None else filtered[: max(0, int(limit))]
        return {
            "seriesId": series_id, "seriesTitle": title, "seasonNumber": season_number,
            "totalReleases": len(releases), "totalFiltered": len(filtered), "returned": len(returned),
            "filters": {
                "qualityContains": quality, "fullSeasonOnly": arguments.get("full_season_only", True),
                "minCustomFormatScore": minimum, "includeRejected": arguments.get("include_rejected", False),
                "downloadAllowed": arguments.get("download_allowed"),
            },
            "releases": [_compact_release(release) for release in returned],
        }

    def _require_client(self) -> Any:
        if self._client is None:
            raise SonarrConnectorError("Sonarr connector is closed")
        return self._client


def create_connector(
    configuration: Mapping[str, Any],
    resolved_secrets: Mapping[str, str],
    *,
    client_factory: Any = PersistentSonarrClient,
) -> SonarrConnectorAdapter:
    """Shared worker factory(configuration, resolvedSecrets)."""
    allowed = {"connectionId", "endpoint", "timeoutS", "nexusSourceRevisionDigest"}
    unknown = set(configuration) - allowed
    if unknown:
        raise ValueError(f"unsupported Sonarr configuration fields: {sorted(unknown)}")
    connection_id = configuration.get("connectionId")
    endpoint = configuration.get("endpoint")
    timeout = configuration.get("timeoutS", 30.0)
    api_key = resolved_secrets.get("api-key")
    if configuration.get("nexusSourceRevisionDigest") != EXPECTED_SOURCE_REVISION_DIGEST:
        raise ValueError("Sonarr source revision does not match gateway acceptance")
    if not isinstance(connection_id, str) or not connection_id:
        raise ValueError("connectionId is required")
    if not isinstance(endpoint, str) or not endpoint.startswith(("http://", "https://")):
        raise ValueError("Sonarr endpoint must be an HTTP(S) URL")
    if not isinstance(api_key, str) or not api_key:
        raise ValueError("resolved api-key is required")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise ValueError("timeoutS must be greater than zero")
    try:
        client = client_factory(base_url=endpoint, api_key=api_key, timeout_s=float(timeout))
        return SonarrConnectorAdapter(connection_id, client)
    except Exception:
        raise SonarrConnectorError("Sonarr connector startup failed") from None


def create_registry() -> Any:
    """Explicit worker-startup registry; importing this module registers nothing."""
    from nexus_connector.registry import ConnectorRegistry

    registry = ConnectorRegistry()
    registry.register("integration.sonarr", create_connector)
    return registry


def _as_int(value: Any, label: str) -> int:
    if value is None:
        raise ValueError(f"{label} is required")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be an integer") from None


def _integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _titles(series: Mapping[str, Any]) -> list[str]:
    values = [series.get("title"), series.get("titleSlug")]
    values.extend(item.get("title") for item in series.get("alternateTitles") or [] if isinstance(item, dict))
    return [str(value) for value in values if value]


def _choose_series(candidates: Any, term: str) -> Mapping[str, Any] | None:
    if not isinstance(candidates, list):
        return None
    valid = [item for item in candidates if isinstance(item, dict) and item.get("id") is not None]
    needle = term.casefold()
    exact = [item for item in valid if any(title.casefold() == needle for title in _titles(item))]
    partial = [item for item in valid if any(needle in title.casefold() for title in _titles(item))]
    return (exact or partial or valid or [None])[0]


def _quality(release: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    wrapper = release.get("quality")
    value = wrapper.get("quality") if isinstance(wrapper, dict) else None
    if not isinstance(value, dict):
        return None, None, None
    return value.get("source"), value.get("name"), value.get("resolution")


def _quality_haystack(release: Mapping[str, Any]) -> str:
    return " ".join(str(value) for value in (*_quality(release), release.get("title")) if value is not None).casefold()


def _score(release: Mapping[str, Any]) -> int:
    return _integer(release.get("customFormatScore"))


def _human_size(size: Any) -> str | None:
    try:
        value = float(size)
    except (TypeError, ValueError):
        return None
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    return f"{int(value)} {units[index]}" if index == 0 else f"{value:.2f} {units[index]}"


def _compact_release(release: Mapping[str, Any]) -> dict[str, Any]:
    source, quality, resolution = _quality(release)
    result = {
        "title": release.get("title"), "releaseName": release.get("title"), "source": source,
        "quality": quality, "resolution": resolution, "customFormatScore": release.get("customFormatScore"),
        "size": release.get("size"), "sizeHuman": _human_size(release.get("size")),
        "indexer": release.get("indexer"), "fullSeason": release.get("fullSeason"),
        "rejected": release.get("rejected"), "rejections": release.get("rejections") or [],
        "downloadAllowed": release.get("downloadAllowed"),
    }
    for key in ("age", "ageHours", "ageMinutes", "seeders", "leechers", "protocol"):
        if release.get(key) is not None:
            result[key] = release[key]
    return result


def _assert_json_safe(value: Any) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        raise SonarrConnectorError("Sonarr returned a non-JSON-safe result") from None
