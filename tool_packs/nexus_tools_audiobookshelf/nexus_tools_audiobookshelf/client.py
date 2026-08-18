"""Shared Audiobookshelf HTTP, authentication, and multipart client."""

from __future__ import annotations

import base64
import http.client
import ipaddress
import json
import mimetypes
import re
import secrets
import socket
import ssl
import unicodedata
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional, Sequence

from nexus.config import get_setting


DEFAULT_TIMEOUT_S = 30.0
DEFAULT_MAX_UPLOAD_BYTES = 20 * 1024 * 1024 * 1024
DEFAULT_USER_AGENT = "Nexus-Audiobookshelf/0.1"
ERROR_BODY_LIMIT = 2048

MEDIA_EXTENSIONS = frozenset(
    {
        ".aac",
        ".abs",
        ".aiff",
        ".azw3",
        ".cbr",
        ".cbz",
        ".epub",
        ".flac",
        ".jpeg",
        ".jpg",
        ".m4a",
        ".m4b",
        ".mobi",
        ".mp3",
        ".mp4",
        ".nfo",
        ".oga",
        ".ogg",
        ".opf",
        ".opus",
        ".pdf",
        ".png",
        ".txt",
        ".wav",
        ".webm",
        ".webma",
        ".webp",
        ".wma",
    }
)
COVER_EXTENSIONS = frozenset({".jpeg", ".jpg", ".png", ".webp"})
BACKUP_EXTENSIONS = frozenset({".audiobookshelf"})
_FIELD_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_RESOLVE_RE = re.compile(r"^(?P<host>[^:]+):(?P<port>[0-9]+):(?P<address>.+)$")
_SENSITIVE_JSON_KEYS = frozenset(
    {
        "apikey",
        "accesstoken",
        "appriseapiurl",
        "refreshtoken",
        "password",
        "pash",
        "token",
        "urls",
    }
)


class AudiobookshelfError(RuntimeError):
    """A redacted Audiobookshelf transport or HTTP failure."""


@dataclass(frozen=True)
class _UploadFile:
    field_name: str
    path: Path
    filename: str
    content_type: str
    size: int


class _MultipartBody:
    """Re-iterable multipart body that streams file bytes in bounded chunks."""

    def __init__(
        self,
        boundary: str,
        fields: Sequence[tuple[str, str]],
        files: Sequence[_UploadFile],
    ) -> None:
        self.boundary = boundary
        self.fields = tuple(fields)
        self.files = tuple(files)
        self.content_length = self._calculate_length()

    @staticmethod
    def _quoted(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _field_prefix(self, name: str, value: str) -> bytes:
        return (
            f"--{self.boundary}\r\n"
            f'Content-Disposition: form-data; name="{self._quoted(name)}"\r\n\r\n'
            f"{value}\r\n"
        ).encode("utf-8")

    def _file_prefix(self, upload: _UploadFile) -> bytes:
        return (
            f"--{self.boundary}\r\n"
            f'Content-Disposition: form-data; name="{self._quoted(upload.field_name)}"; '
            f'filename="{self._quoted(upload.filename)}"\r\n'
            f"Content-Type: {upload.content_type}\r\n\r\n"
        ).encode("utf-8")

    def _closing(self) -> bytes:
        return f"--{self.boundary}--\r\n".encode("ascii")

    def _calculate_length(self) -> int:
        total = sum(len(self._field_prefix(name, value)) for name, value in self.fields)
        for upload in self.files:
            total += len(self._file_prefix(upload)) + upload.size + 2
        return total + len(self._closing())

    def __iter__(self) -> Iterator[bytes]:
        for name, value in self.fields:
            yield self._field_prefix(name, value)
        for upload in self.files:
            yield self._file_prefix(upload)
            with upload.path.open("rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    yield chunk
            yield b"\r\n"
        yield self._closing()


class AudiobookshelfClient:
    """Standard-library Audiobookshelf client with safe direct-connect support."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        *,
        timeout_s: Optional[float] = None,
        resolve: Optional[str] = None,
        upload_roots: Optional[Sequence[str | Path]] = None,
        max_upload_bytes: Optional[int] = None,
    ) -> None:
        self.base_url = (base_url or get_setting("AUDIOBOOKSHELF_URL") or "").strip().rstrip("/")
        self.api_token = (api_token or get_setting("AUDIOBOOKSHELF_API_TOKEN") or "").strip()
        self.timeout_s = self._parse_timeout(
            timeout_s if timeout_s is not None else get_setting("AUDIOBOOKSHELF_TIMEOUT_S")
        )
        self.resolve = (resolve if resolve is not None else get_setting("AUDIOBOOKSHELF_RESOLVE") or "").strip()
        self.max_upload_bytes = self._parse_max_upload_bytes(
            max_upload_bytes
            if max_upload_bytes is not None
            else get_setting("AUDIOBOOKSHELF_MAX_UPLOAD_BYTES")
        )

        if not self.base_url:
            raise ValueError("AUDIOBOOKSHELF_URL is required")
        if not self.api_token:
            raise ValueError("AUDIOBOOKSHELF_API_TOKEN is required")

        parsed = urllib.parse.urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("AUDIOBOOKSHELF_URL must use http or https")
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("AUDIOBOOKSHELF_URL must be an origin URL without credentials, query, or fragment")
        self._scheme = parsed.scheme
        self._host = parsed.hostname
        self._port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._base_path = parsed.path.rstrip("/")
        self._resolve_address = self._parse_resolve(self.resolve)

        configured_roots: Sequence[str | Path]
        if upload_roots is None:
            raw_roots = get_setting("AUDIOBOOKSHELF_UPLOAD_ROOTS") or ""
            configured_roots = [part.strip() for part in raw_roots.split(",") if part.strip()]
        else:
            configured_roots = upload_roots
        self.upload_roots = tuple(self._normalize_upload_root(root) for root in configured_roots)

    @staticmethod
    def _parse_timeout(value: object) -> float:
        if value in (None, ""):
            return DEFAULT_TIMEOUT_S
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("AUDIOBOOKSHELF_TIMEOUT_S must be a number") from exc
        if not 0.1 <= parsed <= 600:
            raise ValueError("AUDIOBOOKSHELF_TIMEOUT_S must be between 0.1 and 600")
        return parsed

    @staticmethod
    def _parse_max_upload_bytes(value: object) -> int:
        if value in (None, ""):
            return DEFAULT_MAX_UPLOAD_BYTES
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("AUDIOBOOKSHELF_MAX_UPLOAD_BYTES must be an integer") from exc
        if parsed < 1:
            raise ValueError("AUDIOBOOKSHELF_MAX_UPLOAD_BYTES must be positive")
        return parsed

    @staticmethod
    def _normalize_upload_root(value: str | Path) -> Path:
        root = Path(value).expanduser()
        if not root.is_absolute():
            raise ValueError("AUDIOBOOKSHELF_UPLOAD_ROOTS entries must be absolute")
        return root.resolve()

    def _parse_resolve(self, value: str) -> Optional[str]:
        if not value:
            return None
        match = _RESOLVE_RE.fullmatch(value)
        if not match:
            raise ValueError("AUDIOBOOKSHELF_RESOLVE must use hostname:port:ip syntax")
        host = match.group("host").lower()
        port = int(match.group("port"))
        address = match.group("address").strip().strip("[]")
        if host != self._host.lower() or port != self._port:
            raise ValueError("AUDIOBOOKSHELF_RESOLVE hostname and port must match AUDIOBOOKSHELF_URL")
        try:
            ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError("AUDIOBOOKSHELF_RESOLVE must end with a literal IP address") from exc
        return address

    @staticmethod
    def segment(value: object, *, name: str = "identifier") -> str:
        text = str(value)
        if not text or text in {".", ".."} or any(ord(char) < 32 for char in text):
            raise ValueError(f"{name} must be a non-empty path segment")
        return urllib.parse.quote(text, safe="")

    @staticmethod
    def _encode_params(params: Optional[Mapping[str, Any]]) -> str:
        if not params:
            return ""
        encoded: list[tuple[str, str]] = []
        for key, value in params.items():
            if value is None:
                continue
            values: Iterable[Any] = value if isinstance(value, (list, tuple)) else (value,)
            for item in values:
                if item is None:
                    continue
                if isinstance(item, bool):
                    # Audiobookshelf 2.36.0 controllers consistently parse
                    # boolean query flags as numeric strings.
                    rendered = "1" if item else "0"
                else:
                    rendered = str(item)
                encoded.append((str(key), rendered))
        return urllib.parse.urlencode(encoded, doseq=True)

    def _request_target(
        self,
        endpoint: str,
        *,
        api_path: Optional[str],
        params: Optional[Mapping[str, Any]],
    ) -> str:
        parsed_endpoint = urllib.parse.urlsplit(endpoint)
        if parsed_endpoint.scheme or parsed_endpoint.netloc or parsed_endpoint.query or parsed_endpoint.fragment:
            raise ValueError("endpoint must be a relative path without query or fragment")
        path_parts = [part for part in parsed_endpoint.path.split("/") if part]
        if any(part in {".", ".."} for part in path_parts):
            raise ValueError("endpoint traversal segments are not allowed")
        prefix = "/api" if api_path is None else "/" + api_path.strip("/") if api_path else ""
        path = "/".join(part for part in (self._base_path.strip("/"), prefix.strip("/"), "/".join(path_parts)) if part)
        target = "/" + path
        query = self._encode_params(params)
        return f"{target}?{query}" if query else target

    def _connection(self) -> http.client.HTTPConnection:
        if self._scheme == "https":
            connection: http.client.HTTPConnection = http.client.HTTPSConnection(
                self._host,
                self._port,
                timeout=self.timeout_s,
                context=ssl.create_default_context(),
            )
        else:
            connection = http.client.HTTPConnection(self._host, self._port, timeout=self.timeout_s)

        if self._resolve_address:
            address = self._resolve_address
            port = self._port

            def create_connection(
                _target: tuple[str, int],
                timeout: object = socket._GLOBAL_DEFAULT_TIMEOUT,
                source_address: Optional[tuple[str, int]] = None,
                **kwargs: Any,
            ) -> socket.socket:
                return socket.create_connection(
                    (address, port),
                    timeout=timeout,
                    source_address=source_address,
                    **kwargs,
                )

            connection._create_connection = create_connection  # type: ignore[attr-defined]
        return connection

    def _redact(self, text: str) -> str:
        redacted = text.replace(self.api_token, "[REDACTED]") if self.api_token else text
        redacted = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+", r"\1[REDACTED]", redacted)
        redacted = re.sub(
            r'(?i)(["\']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|pash|token)'
            r'["\']?\s*[:=]\s*)(["\']?)[^"\'\s,;}]+',
            r'\1\2[REDACTED]',
            redacted,
        )
        return redacted

    def _decode_response(self, raw: bytes, content_type: str) -> Any:
        if not raw:
            return None
        charset = "utf-8"
        match = re.search(r"charset=([^;\s]+)", content_type, re.IGNORECASE)
        if match:
            charset = match.group(1).strip('"')
        try:
            text = raw.decode(charset)
        except (LookupError, UnicodeDecodeError):
            return {
                "contentType": content_type or "application/octet-stream",
                "size": len(raw),
                "base64": base64.b64encode(raw).decode("ascii"),
            }
        if "json" in content_type.lower():
            try:
                return self._sanitize_json(json.loads(text))
            except json.JSONDecodeError:
                return self._redact(text)
        try:
            return self._sanitize_json(json.loads(text))
        except json.JSONDecodeError:
            return self._redact(text)

    def _sanitize_json(self, value: Any) -> Any:
        """Recursively redact credentials returned by administrative endpoints."""

        if isinstance(value, Mapping):
            sanitized: Dict[str, Any] = {}
            for key, item in value.items():
                rendered_key = str(key)
                normalized_key = re.sub(r"[^a-z0-9]", "", rendered_key.casefold())
                if normalized_key in _SENSITIVE_JSON_KEYS or normalized_key.endswith("token"):
                    sanitized[rendered_key] = "[REDACTED]" if item not in (None, "") else item
                else:
                    sanitized[rendered_key] = self._sanitize_json(item)
            return sanitized
        if isinstance(value, list):
            return [self._sanitize_json(item) for item in value]
        if isinstance(value, tuple):
            return [self._sanitize_json(item) for item in value]
        if isinstance(value, str):
            return self._redact(value)
        return value

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[Any] = None,
        api_path: Optional[str] = None,
        authenticated: bool = True,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        normalized_method = method.upper()
        target = self._request_target(endpoint, api_path=api_path, params=params)
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if authenticated:
            headers["Authorization"] = f"Bearer {self.api_token}"
        if extra_headers:
            headers.update({str(key): str(value) for key, value in extra_headers.items()})

        encoded_body: Optional[bytes | Iterable[bytes]] = None
        if body is not None:
            if isinstance(body, (bytes, bytearray)):
                encoded_body = bytes(body)
            elif isinstance(body, _MultipartBody):
                encoded_body = body
                headers.setdefault("Content-Type", f"multipart/form-data; boundary={body.boundary}")
                headers.setdefault("Content-Length", str(body.content_length))
            else:
                try:
                    encoded_body = json.dumps(
                        body,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode("utf-8")
                except (TypeError, ValueError) as exc:
                    raise ValueError("body must be strictly JSON serializable") from exc
                headers.setdefault("Content-Type", "application/json")
            if isinstance(encoded_body, bytes):
                headers.setdefault("Content-Length", str(len(encoded_body)))

        connection = self._connection()
        try:
            connection.request(normalized_method, target, body=encoded_body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            content_type = response.getheader("Content-Type", "") or ""
            if response.status >= 400:
                detail = self._redact(raw[:ERROR_BODY_LIMIT].decode("utf-8", errors="replace"))
                message = f"Audiobookshelf {normalized_method} {target.split('?', 1)[0]} failed with HTTP {response.status}"
                if detail.strip():
                    message += f": {detail.strip()}"
                raise AudiobookshelfError(message)
            return self._decode_response(raw, content_type)
        except AudiobookshelfError:
            raise
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            detail = self._redact(str(exc))
            raise AudiobookshelfError(
                f"Audiobookshelf {normalized_method} {target.split('?', 1)[0]} transport failure: {detail}"
            ) from exc
        finally:
            connection.close()

    def get(
        self,
        endpoint: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
        authenticated: bool = True,
    ) -> Any:
        return self.request("GET", endpoint, params=params, api_path=api_path, authenticated=authenticated)

    def post(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
    ) -> Any:
        return self.request("POST", endpoint, params=params, body=body, api_path=api_path)

    def patch(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        *,
        api_path: Optional[str] = None,
    ) -> Any:
        return self.request("PATCH", endpoint, params=params, body=body, api_path=api_path)

    def delete(
        self,
        endpoint: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        body: Optional[Any] = None,
        api_path: Optional[str] = None,
    ) -> Any:
        return self.request("DELETE", endpoint, params=params, body=body, api_path=api_path)

    def _validated_upload(
        self,
        value: str | Path,
        *,
        field_name: str,
        allowed_extensions: frozenset[str],
    ) -> _UploadFile:
        if not self.upload_roots:
            raise ValueError("AUDIOBOOKSHELF_UPLOAD_ROOTS must allowlist at least one absolute directory")
        if not _FIELD_NAME_RE.fullmatch(field_name):
            raise ValueError("multipart field name contains unsupported characters")
        requested = Path(value).expanduser()
        try:
            path = requested.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"upload file is not accessible: {requested.name}") from exc
        if not path.is_file():
            raise ValueError(f"upload path is not a regular file: {path.name}")
        if not any(path == root or path.is_relative_to(root) for root in self.upload_roots):
            raise ValueError(f"upload path is outside AUDIOBOOKSHELF_UPLOAD_ROOTS: {path.name}")
        suffix = path.suffix.lower()
        if suffix not in allowed_extensions:
            raise ValueError(f"unsupported upload extension: {suffix or '[none]'}")
        size = path.stat().st_size
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        safe_filename = "".join(char for char in path.name if ord(char) >= 32).replace("/", "_").replace("\\", "_")
        return _UploadFile(field_name, path, safe_filename, content_type, size)

    def multipart(
        self,
        endpoint: str,
        *,
        fields: Optional[Mapping[str, Any]],
        files: Sequence[tuple[str, str | Path]],
        allowed_extensions: frozenset[str],
    ) -> Any:
        if not files:
            raise ValueError("at least one upload file is required")
        normalized_fields: list[tuple[str, str]] = []
        for name, value in (fields or {}).items():
            if not _FIELD_NAME_RE.fullmatch(str(name)):
                raise ValueError("multipart field name contains unsupported characters")
            if value is None:
                continue
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            elif isinstance(value, (dict, list, tuple)):
                rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            else:
                rendered = str(value)
            normalized_fields.append((str(name), rendered))

        uploads = [
            self._validated_upload(path, field_name=name, allowed_extensions=allowed_extensions)
            for name, path in files
        ]
        boundary = "nexus-abs-" + secrets.token_hex(16)
        stream = _MultipartBody(boundary, normalized_fields, uploads)
        if stream.content_length > self.max_upload_bytes:
            raise ValueError("multipart upload exceeds AUDIOBOOKSHELF_MAX_UPLOAD_BYTES")
        return self.request("POST", endpoint, body=stream)

    def upload_media(
        self,
        *,
        title: str,
        library_id: str,
        folder_id: str,
        file_paths: Sequence[str | Path],
        author: Optional[str] = None,
        series: Optional[str] = None,
    ) -> Any:
        fields = {
            "title": title,
            "library": library_id,
            "folder": folder_id,
            "author": author,
            "series": series,
        }
        files = [(str(index), path) for index, path in enumerate(file_paths)]
        return self.multipart("upload", fields=fields, files=files, allowed_extensions=MEDIA_EXTENSIONS)

    def upload_cover(self, item_id: str, file_path: str | Path) -> Any:
        return self.multipart(
            f"items/{self.segment(item_id, name='item_id')}/cover",
            fields=None,
            files=[("cover", file_path)],
            allowed_extensions=COVER_EXTENSIONS,
        )

    def upload_backup(self, file_path: str | Path) -> Any:
        return self.multipart(
            "backups/upload",
            fields=None,
            files=[("file", file_path)],
            allowed_extensions=BACKUP_EXTENSIONS,
        )

    @staticmethod
    def _nested(mapping: Mapping[str, Any], *parts: str) -> Any:
        value: Any = mapping
        for part in parts:
            if not isinstance(value, Mapping):
                return None
            value = value.get(part)
        return value

    @staticmethod
    def _normalized_text(value: object) -> str:
        text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
        return " ".join(text.split())

    def find_duplicate_items(
        self,
        library_id: str,
        *,
        keys: Sequence[str] = ("path", "asin", "isbn", "title_author"),
        max_items: int = 10000,
        page_size: int = 500,
    ) -> Dict[str, Any]:
        allowed_keys = {"path", "asin", "isbn", "title_author"}
        selected_keys = tuple(dict.fromkeys(keys))
        if not selected_keys or any(key not in allowed_keys for key in selected_keys):
            raise ValueError("keys must contain one or more of path, asin, isbn, title_author")
        if not 1 <= max_items <= 100000 or not 1 <= page_size <= 1000:
            raise ValueError("max_items must be 1..100000 and page_size must be 1..1000")

        item_groups: Dict[tuple[str, str], list[Dict[str, Any]]] = {}
        scanned = 0
        page = 0
        reported_total: Optional[int] = None
        while scanned < max_items:
            limit = min(page_size, max_items - scanned)
            payload = self.get(
                f"libraries/{self.segment(library_id, name='library_id')}/items",
                params={"limit": limit, "page": page, "minified": True},
            )
            if not isinstance(payload, Mapping):
                raise AudiobookshelfError("library items response is not an object")
            results = payload.get("results")
            if not isinstance(results, list):
                raise AudiobookshelfError("library items response has no results array")
            total_value = payload.get("total")
            if isinstance(total_value, int):
                reported_total = total_value
            for item in results:
                if not isinstance(item, Mapping):
                    continue
                metadata = self._nested(item, "media", "metadata")
                metadata = metadata if isinstance(metadata, Mapping) else {}
                item_id = str(item.get("id") or "")
                summary = {
                    "id": item_id,
                    "path": item.get("path"),
                    "title": metadata.get("title"),
                    "authors": metadata.get("authors") or metadata.get("authorName"),
                    "asin": metadata.get("asin"),
                    "isbn": metadata.get("isbn"),
                }
                candidates: Dict[str, Any] = {
                    "path": item.get("path"),
                    "asin": metadata.get("asin"),
                    "isbn": metadata.get("isbn"),
                }
                authors = metadata.get("authors") or metadata.get("authorName") or ""
                if isinstance(authors, list):
                    authors = ",".join(
                        str(author.get("name") if isinstance(author, Mapping) else author)
                        for author in authors
                    )
                candidates["title_author"] = (
                    f"{self._normalized_text(metadata.get('title') or '')}"
                    f"\x00{self._normalized_text(authors)}"
                )
                for key in selected_keys:
                    raw_candidate = candidates.get(key) or ""
                    normalized = (
                        str(raw_candidate)
                        if key == "title_author"
                        else self._normalized_text(raw_candidate)
                    )
                    if normalized and normalized != "\x00":
                        item_groups.setdefault((key, normalized), []).append(summary)
            scanned += len(results)
            if len(results) < limit or (reported_total is not None and scanned >= reported_total):
                break
            page += 1

        duplicates = [
            {"key": key, "value": value, "count": len(items), "items": items}
            for (key, value), items in sorted(item_groups.items())
            if len(items) > 1
        ]
        return {
            "libraryId": library_id,
            "scanned": scanned,
            "reportedTotal": reported_total,
            "truncated": reported_total is not None and scanned < reported_total,
            "duplicateGroupCount": len(duplicates),
            "groups": duplicates,
        }


_default_client: Optional[AudiobookshelfClient] = None
_default_client_key: Optional[tuple[object, ...]] = None


def get_client() -> AudiobookshelfClient:
    """Return a cached client keyed by every connection and upload setting."""

    global _default_client, _default_client_key
    base_url = get_setting("AUDIOBOOKSHELF_URL") or ""
    token = get_setting("AUDIOBOOKSHELF_API_TOKEN") or ""
    timeout = get_setting("AUDIOBOOKSHELF_TIMEOUT_S") or ""
    resolve = get_setting("AUDIOBOOKSHELF_RESOLVE") or ""
    roots = get_setting("AUDIOBOOKSHELF_UPLOAD_ROOTS") or ""
    max_bytes = get_setting("AUDIOBOOKSHELF_MAX_UPLOAD_BYTES") or ""
    key = (base_url, token, timeout, resolve, roots, max_bytes)
    if _default_client is None or _default_client_key != key:
        _default_client = AudiobookshelfClient(
            base_url=base_url,
            api_token=token,
            timeout_s=timeout or None,
            resolve=resolve,
            upload_roots=[part.strip() for part in roots.split(",") if part.strip()],
            max_upload_bytes=max_bytes or None,
        )
        _default_client_key = key
    return _default_client
