"""Authenticated local file staging for the Streamable HTTP wrapper."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from starlette.requests import Request
from starlette.responses import JSONResponse

from nexus.env import get_setting
from nexus.http_auth import NexusBearerVerifier


DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_TTL_SECONDS = 24 * 60 * 60
DEFAULT_QUOTA_BYTES = 256 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
MIME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}$")
ARTIFACT_RE = re.compile(r"^[0-9a-f]{32}$")
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")
ALLOWED_EXTENSIONS = {
    ".aac", ".avi", ".bmp", ".csv", ".doc", ".docx", ".eml", ".epub", ".flac",
    ".gif", ".heic", ".htm", ".html", ".jpeg", ".jpg", ".json", ".log", ".m4a",
    ".m4b", ".md", ".mkv", ".mov", ".mp3", ".mp4", ".mpeg", ".odp", ".ods",
    ".odt", ".ogg", ".opus", ".pdf", ".png", ".ppt", ".pptx", ".rtf", ".tif",
    ".tiff", ".tsv", ".txt", ".wav", ".webm", ".webp", ".xls", ".xlsx", ".xml",
    ".yaml", ".yml", ".zip",
}


@dataclass(frozen=True)
class FileStagingConfig:
    root: Path
    max_bytes: int = DEFAULT_MAX_BYTES
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    quota_bytes: int = DEFAULT_QUOTA_BYTES
    allowed_extensions: frozenset[str] = frozenset(ALLOWED_EXTENSIONS)


def _int_setting(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = get_setting(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value < minimum or value > maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


def load_file_staging_config() -> FileStagingConfig | None:
    root = get_setting("NEXUS_FILE_STAGING_ROOT")
    if not root:
        return None
    root_path = Path(root).expanduser()
    if not root_path.is_absolute():
        raise RuntimeError("NEXUS_FILE_STAGING_ROOT must be an absolute path")
    raw_extensions = get_setting("NEXUS_FILE_STAGING_ALLOWED_EXTENSIONS")
    allowed_extensions = frozenset(ALLOWED_EXTENSIONS)
    if raw_extensions:
        parsed_extensions = {
            value if value.startswith(".") else f".{value}"
            for item in raw_extensions.split(",")
            if (value := item.strip().lower())
        }
        if not parsed_extensions or any(
            not re.fullmatch(r"\.[a-z0-9]{1,12}", value)
            for value in parsed_extensions
        ):
            raise RuntimeError(
                "NEXUS_FILE_STAGING_ALLOWED_EXTENSIONS must be a comma-separated "
                "list of simple file extensions"
            )
        allowed_extensions = frozenset(parsed_extensions)
    return FileStagingConfig(
        root=root_path,
        max_bytes=_int_setting("NEXUS_FILE_STAGING_MAX_BYTES", DEFAULT_MAX_BYTES, 1, 512 * 1024 * 1024),
        ttl_seconds=_int_setting("NEXUS_FILE_STAGING_TTL_SECONDS", DEFAULT_TTL_SECONDS, 60, 7 * 24 * 60 * 60),
        quota_bytes=_int_setting("NEXUS_FILE_STAGING_QUOTA_BYTES", DEFAULT_QUOTA_BYTES, 1, 10 * 1024 * 1024 * 1024),
        allowed_extensions=allowed_extensions,
    )


class FileStagingService:
    def __init__(self, config: FileStagingConfig, verifier: NexusBearerVerifier) -> None:
        self.config = config
        self.verifier = verifier
        self._cleanup_task: asyncio.Task[None] | None = None
        self._client_locks: dict[str, asyncio.Lock] = {}

    def start(self) -> None:
        if self.config.root.is_symlink():
            raise RuntimeError("NEXUS_FILE_STAGING_ROOT must not be a symlink")
        self.config.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.config.root.is_dir():
            raise RuntimeError("NEXUS_FILE_STAGING_ROOT must be a directory")
        os.chmod(self.config.root, 0o700)
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        if self._cleanup_task is None:
            return
        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass

    async def upload(self, request: Request) -> JSONResponse:
        client = self._client_from_request(request)
        if client is None:
            return _error(401, "unauthorized")
        try:
            filename = _safe_filename(
                request.headers.get("x-nexus-filename", ""),
                allowed_extensions=self.config.allowed_extensions,
            )
            content_type = _safe_content_type(request.headers.get("content-type", "application/octet-stream"))
            claimed_length = _content_length(request.headers.get("content-length"), self.config.max_bytes)
            async with self._client_locks.setdefault(client, asyncio.Lock()):
                await self.cleanup_expired()
                client_dir = self._client_dir(client)
                client_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(client_dir, 0o700)
                if _directory_size(client_dir) + claimed_length > self.config.quota_bytes:
                    return _error(413, "quota_exceeded")
                artifact_id = uuid.uuid4().hex
                suffix = Path(filename).suffix.lower()
                final_path = client_dir / f"{artifact_id}{suffix}"
                tmp_path = client_dir / f".{artifact_id}.tmp"
                meta_path = self._meta_path(client_dir, artifact_id)
                meta_tmp_path = meta_path.with_suffix(".json.tmp")
                digest = hashlib.sha256()
                size = 0
                try:
                    with tmp_path.open("xb") as handle:
                        os.chmod(tmp_path, 0o600)
                        async for chunk in request.stream():
                            size += len(chunk)
                            if size > self.config.max_bytes:
                                return _cleanup_and_error(tmp_path, 413, "too_large")
                            digest.update(chunk)
                            handle.write(chunk)
                    if size == 0:
                        return _cleanup_and_error(tmp_path, 400, "empty_file")
                    if size != claimed_length:
                        return _cleanup_and_error(tmp_path, 400, "content_length_mismatch")
                    metadata = self._metadata(
                        artifact_id=artifact_id,
                        client=client,
                        filename=filename,
                        content_type=content_type,
                        size=size,
                        sha256=digest.hexdigest(),
                        path=final_path,
                    )
                    meta_tmp_path.write_text(
                        json.dumps(metadata, sort_keys=True, separators=(",", ":")),
                        encoding="utf-8",
                    )
                    os.chmod(meta_tmp_path, 0o600)
                    meta_tmp_path.replace(meta_path)
                    tmp_path.replace(final_path)
                except BaseException:
                    tmp_path.unlink(missing_ok=True)
                    meta_tmp_path.unlink(missing_ok=True)
                    meta_path.unlink(missing_ok=True)
                    final_path.unlink(missing_ok=True)
                    raise
                return JSONResponse(metadata, status_code=201)
        except StagingRequestError as exc:
            return _error(exc.status_code, exc.code)
        except ValueError as exc:
            return _error(400, str(exc))

    async def delete(self, request: Request) -> JSONResponse:
        client = self._client_from_request(request)
        if client is None:
            return _error(401, "unauthorized")
        artifact_id = request.path_params["artifact_id"]
        if not ARTIFACT_RE.fullmatch(artifact_id):
            return _error(404, "not_found")
        client_dir = self._client_dir(client)
        removed = False
        if client_dir.exists() and not client_dir.is_symlink():
            for path in client_dir.glob(f"{artifact_id}*"):
                if path.is_file() and not path.is_symlink():
                    path.unlink(missing_ok=True)
                    removed = True
        meta = self._meta_path(client_dir, artifact_id, create=False)
        if meta.is_file() and not meta.is_symlink():
            meta.unlink(missing_ok=True)
            removed = True
        return JSONResponse({"success": True, "deleted": removed, "artifact_id": artifact_id})

    async def cleanup_expired(self) -> None:
        now = time.time()
        if not self.config.root.exists():
            return
        for meta_path in self.config.root.glob("*/metadata/*.json"):
            if meta_path.is_symlink() or not meta_path.is_file():
                continue
            try:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if float(metadata.get("expires_at_epoch", 0)) > now:
                continue
            path = Path(str(metadata.get("path", "")))
            if _is_child(path, self.config.root) and path.is_file() and not path.is_symlink():
                path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
        stale_before = now - self.config.ttl_seconds
        for pattern in ("*/.*.tmp", "*/metadata/*.json.tmp"):
            for tmp_path in self.config.root.glob(pattern):
                if tmp_path.is_symlink() or not tmp_path.is_file():
                    continue
                try:
                    if tmp_path.stat().st_mtime < stale_before:
                        tmp_path.unlink(missing_ok=True)
                except OSError:
                    continue
        self._cleanup_orphaned_temps(now)

    def _metadata(
        self,
        *,
        artifact_id: str,
        client: str,
        filename: str,
        content_type: str,
        size: int,
        sha256: str,
        path: Path,
    ) -> dict[str, Any]:
        created_at = time.time()
        expires_at = created_at + self.config.ttl_seconds
        return {
            "artifact_id": artifact_id,
            "path": str(path),
            "filename": filename,
            "content_type": content_type,
            "size": size,
            "sha256": sha256,
            "client": client,
            "created_at": _iso_utc(created_at),
            "expires_at": _iso_utc(expires_at),
            "expires_at_epoch": expires_at,
        }

    def _client_from_request(self, request: Request) -> str | None:
        auth = request.headers.get("authorization", "")
        prefix = "Bearer "
        if not auth.startswith(prefix):
            return None
        return self.verifier.client_fingerprint_for_token(auth[len(prefix) :].strip())

    def _client_dir(self, client: str) -> Path:
        return self.config.root / client

    def _meta_path(self, client_dir: Path, artifact_id: str, *, create: bool = True) -> Path:
        meta_dir = client_dir / "metadata"
        if create:
            meta_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(meta_dir, 0o700)
        return meta_dir / f"{artifact_id}.json"

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(300)
            await self.cleanup_expired()

    def _cleanup_orphaned_temps(self, now: float) -> None:
        cutoff = now - min(self.config.ttl_seconds, 24 * 60 * 60)
        for path in self.config.root.glob("*/*"):
            if path.is_symlink() or not path.is_file() or not path.name.startswith("."):
                continue
            if not path.name.endswith((".tmp", ".json.tmp")):
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
            except OSError:
                continue


class StagingRequestError(ValueError):
    def __init__(self, status_code: int, code: str) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code


def _safe_filename(
    raw: str,
    *,
    allowed_extensions: frozenset[str] = frozenset(ALLOWED_EXTENSIONS),
) -> str:
    if not raw:
        raise ValueError("missing_filename")
    decoded = unquote(raw)
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in decoded):
        raise ValueError("invalid_filename")
    if decoded in {".", ".."} or "/" in decoded or "\\" in decoded:
        raise ValueError("invalid_filename")
    name = Path(decoded).name.strip().strip(".")
    name = SAFE_NAME_RE.sub("_", name)[:160]
    if not name:
        raise ValueError("invalid_filename")
    ext = Path(name).suffix.lower()
    if ext not in allowed_extensions:
        raise ValueError("extension_not_allowed")
    return name


def _safe_content_type(raw: str) -> str:
    content_type = raw.split(";", 1)[0].strip().lower()
    if not MIME_RE.fullmatch(content_type):
        raise ValueError("invalid_content_type")
    return content_type


def _content_length(raw: str | None, max_bytes: int) -> int:
    if not raw:
        raise ValueError("missing_content_length")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("invalid_content_length") from exc
    if value <= 0:
        raise ValueError("empty_file")
    if value > max_bytes:
        raise StagingRequestError(413, "too_large")
    return value


def _directory_size(path: Path) -> int:
    total = 0
    for item in path.glob("*"):
        if item.is_file() and not item.is_symlink():
            total += item.stat().st_size
    return total


def _is_child(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _iso_utc(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))


def _error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"success": False, "error": code}, status_code=status)


def _cleanup_and_error(path: Path, status: int, code: str) -> JSONResponse:
    path.unlink(missing_ok=True)
    return _error(status, code)
