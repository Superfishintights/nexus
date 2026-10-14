"""Shared, synchronous Vikunja API v2 client. No import-time network activity."""
from __future__ import annotations

import json
import hashlib
import http.client
import math
import mimetypes
import os
from pathlib import Path
import re
from typing import Any, Callable
import urllib.error
import urllib.parse
import urllib.request
import uuid

from nexus.config import get_setting


class VikunjaError(RuntimeError):
    """A sanitized API or transport failure."""
    def __init__(self, message: str, *, status: int | None = None, code: Any = None):
        super().__init__(message)
        self.status = status
        self.code = code


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A configured endpoint must not forward a bearer token elsewhere.
        return None


def positive_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("Resource IDs must be positive integers")
    return value


def path_text(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Path text must be a nonempty string")
    return urllib.parse.quote(value, safe="")


def _token_setting() -> str:
    token = get_setting("VIKUNJA_TOKEN") or ""
    if token:
        return str(token).strip()
    token_file = get_setting("VIKUNJA_TOKEN_FILE")
    if token_file:
        try:
            path = Path(str(token_file)).expanduser()
            if path.stat().st_mode & 0o077:
                raise ValueError("VIKUNJA_TOKEN_FILE must have private permissions, such as 0600")
            return path.read_text().strip()
        except OSError:
            raise ValueError("Cannot read VIKUNJA_TOKEN_FILE") from None
    return ""


class VikunjaClient:
    def __init__(self, base_url: str, token: str = "", *, timeout_s: float = 30.0):
        base_url = base_url.strip().rstrip("/")
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("VIKUNJA_URL must be an http(s) URL without credentials, query or fragment")
        if parsed.path.rstrip("/").endswith("/api/v1"):
            raise ValueError("This pack requires API v2; VIKUNJA_URL points at v1")
        self.api_url = base_url if parsed.path.rstrip("/").endswith("/api/v2") else base_url + "/api/v2"
        self.token = token.strip()
        if "\n" in self.token or "\r" in self.token:
            raise ValueError("VIKUNJA_TOKEN must be a single-line token")
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("VIKUNJA_TIMEOUT_S must be a positive finite number")
        self.timeout_s = timeout_s
        self._opener = urllib.request.build_opener(_NoRedirect())

    def request(self, method: str, endpoint: str, *, params: dict[str, Any] | None = None,
                body: Any = None, authenticated: bool = True, headers: dict[str, str] | None = None,
                raw_body: bytes | None = None, _response_handler: Callable[[Any], Any] | None = None) -> Any:
        if authenticated and not self.token:
            raise ValueError("VIKUNJA_TOKEN or VIKUNJA_TOKEN_FILE is required")
        if endpoint.startswith("/") or "://" in endpoint or any(part in {".", ".."} for part in endpoint.split("/")):
            raise ValueError("Endpoint must be a relative API path")
        url = self.api_url + "/" + endpoint
        query = {}
        for k, v in (params or {}).items():
            if v is not None:
                def scalar(x):
                    return str(x).lower() if isinstance(x, bool) else str(x)
                query[k] = [scalar(x) for x in v if x is not None] if isinstance(v, (list, tuple)) else scalar(v)
        if query:
            url += "?" + urllib.parse.urlencode(query, doseq=True)
        req_headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if authenticated:
            req_headers["Authorization"] = "Bearer " + self.token
        req_headers.update(headers or {})
        if body is not None and raw_body is not None:
            raise ValueError("Specify either a JSON body or raw bytes, not both")
        data = raw_body if raw_body is not None else None if body is None else json.dumps(body, allow_nan=False).encode()
        request = urllib.request.Request(url, data=data, method=method, headers=req_headers)
        try:
            with self._opener.open(request, timeout=self.timeout_s) as response:
                if _response_handler is not None:
                    return _response_handler(response)
                raw = response.read()
                if not raw:
                    return None
                try:
                    return json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    raise VikunjaError("Vikunja returned a non-JSON response; check the API URL and reverse proxy") from None
        except urllib.error.HTTPError as exc:
            detail, code = "API request failed", None
            try:
                error = json.loads(exc.read())
                detail = str(error.get("detail") or error.get("message") or error.get("title") or detail)
                code = error.get("code")
            except (ValueError, UnicodeDecodeError, AttributeError):
                pass
            if self.token:
                detail = detail.replace(self.token, "[redacted]")
            for secret in _body_credentials(body):
                detail = detail.replace(secret, "[redacted]")
            raise VikunjaError(f"Vikunja HTTP {exc.code}: {detail[:500]}", status=exc.code, code=code) from None
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            raise VikunjaError("Vikunja transport failed; check endpoint, network and timeout") from None

    def upload_attachments(self, task_id: int, file_paths: list[str]) -> Any:
        """Upload bounded files from the configured runtime attachment directory."""
        task_id = positive_id(task_id)
        if not isinstance(file_paths, list) or not 1 <= len(file_paths) <= 10:
            raise ValueError("file_paths must contain 1 to 10 runtime-local paths")
        root = attachment_directory()
        limit = attachment_byte_limit()
        payloads, total = [], 0
        for file_path in file_paths:
            if not isinstance(file_path, str):
                raise ValueError("Each attachment path must be a string")
            source = Path(file_path).expanduser()
            source = source if source.is_absolute() else root / source
            try:
                source = source.resolve(strict=True)
                source.relative_to(root)
            except (OSError, ValueError):
                raise ValueError("Upload files must exist within VIKUNJA_ATTACHMENT_DIR") from None
            if not source.is_file() or any(ch in source.name for ch in '\r\n"'):
                raise ValueError("Upload source must be a regular file with a safe filename")
            with source.open("rb") as uploaded:
                content = uploaded.read(limit - total + 1)
            total += len(content)
            if total > limit:
                raise ValueError("Attachment upload exceeds VIKUNJA_MAX_ATTACHMENT_BYTES")
            payloads.append((source.name, mimetypes.guess_type(source.name)[0] or "application/octet-stream", content))
        boundary = "vikunja-" + uuid.uuid4().hex
        parts = []
        for name, mime, content in payloads:
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n').encode() + content + b"\r\n")
        multipart = b"".join(parts) + f"--{boundary}--\r\n".encode()
        return self.request("POST", f"tasks/{task_id}/attachments", raw_body=multipart,
                            headers={"Content-Type": "multipart/form-data; boundary=" + boundary})

    def download_attachment(self, task_id: int, attachment_id: int, output_name: str,
                            *, preview_size: str | None = None) -> dict[str, Any]:
        task_id, attachment_id = positive_id(task_id), positive_id(attachment_id)
        if preview_size not in {None, "sm", "md", "lg", "xl"}:
            raise ValueError("preview_size must be sm, md, lg or xl")
        destination = _new_output_path(attachment_directory(), output_name)
        limit = attachment_byte_limit()

        def consume(response):
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > limit:
                raise ValueError("Attachment download exceeds VIKUNJA_MAX_ATTACHMENT_BYTES")
            created, complete, total = False, False, 0
            digest = hashlib.sha256()
            try:
                fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                created = True
                with os.fdopen(fd, "wb") as output:
                    while True:
                        chunk = response.read(min(65536, limit - total + 1))
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > limit:
                            raise ValueError("Attachment download exceeds VIKUNJA_MAX_ATTACHMENT_BYTES")
                        output.write(chunk)
                        digest.update(chunk)
                if length is not None and total != int(length):
                    raise VikunjaError("Attachment download ended before the declared size; partial file removed")
                complete = True
                return {"task_id": task_id, "attachment_id": attachment_id, "file_path": str(destination),
                        "size_bytes": total, "sha256": digest.hexdigest(),
                        "content_type": response.headers.get("Content-Type", "application/octet-stream")}
            finally:
                if created and not complete:
                    destination.unlink(missing_ok=True)

        return self.request("GET", f"tasks/{task_id}/attachments/{attachment_id}",
                            params={"preview_size": preview_size}, headers={"Accept": "application/octet-stream"},
                            _response_handler=consume)

    def page(self, endpoint: str, *, page: int = 1, per_page: int = 50, params: dict[str, Any] | None = None) -> dict[str, Any]:
        positive_id(page)
        positive_id(per_page)
        data = self.request("GET", endpoint, params={**(params or {}), "page": page, "per_page": per_page})
        if not isinstance(data, dict) or "items" not in data or data.get("items") is not None and not isinstance(data.get("items"), list):
            raise VikunjaError("Expected the API v2 pagination envelope")
        current = data.get("page", page)
        total_pages = data.get("total_pages", 0)
        return {"items": data.get("items") or [], "pagination": {
            "page": current, "per_page": data.get("per_page", per_page),
            "total": data.get("total"), "total_pages": total_pages,
            "next_page": current + 1 if current < total_pages else None,
        }}

    def all_pages(self, endpoint: str, *, params: dict[str, Any] | None = None, max_pages: int = 100, per_page: int = 50) -> dict[str, Any]:
        positive_id(max_pages)
        if max_pages > 1000:
            raise ValueError("max_pages must be at most 1000")
        items, current = [], 1
        while True:
            result = self.page(endpoint, page=current, per_page=per_page, params=params)
            items.extend(result["items"])
            next_page = result["pagination"]["next_page"]
            if next_page is None or current >= max_pages:
                return {"items": items, "pages_fetched": current, "truncated": next_page is not None,
                        "next_page": next_page, "total": result["pagination"]["total"]}
            current = next_page


def get_client() -> VikunjaClient:
    # Read config and token file afresh so rotation never needs a Python restart.
    url = str(get_setting("VIKUNJA_URL") or "")
    if not url:
        raise ValueError("VIKUNJA_URL is required")
    return VikunjaClient(url, _token_setting(), timeout_s=float(get_setting("VIKUNJA_TIMEOUT_S") or 30))


def fields_body(title: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be nonempty")
    if fields is not None and not isinstance(fields, dict):
        raise ValueError("fields must be an object")
    return {**(fields or {}), "title": title}


def validate_marker(marker: str) -> str:
    if not re.fullmatch(r"\[personal-agent:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\]", marker):
        raise ValueError("marker must be an exact [personal-agent:<UUID>] ownership marker")
    return marker


def token_output_path(output_name: str) -> Path:
    directory = get_setting("VIKUNJA_TOKEN_OUTPUT_DIR")
    if not directory:
        raise ValueError("VIKUNJA_TOKEN_OUTPUT_DIR must be set before creating a token")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", output_name):
        raise ValueError("output_name must be a simple filename")
    root = Path(str(directory)).expanduser()
    if not root.is_dir() or root.stat().st_mode & 0o077:
        raise ValueError("VIKUNJA_TOKEN_OUTPUT_DIR must exist with private permissions, such as 0700")
    destination = root / output_name
    if destination.exists() or destination.is_symlink():
        raise ValueError("Token output file already exists; choose a new output_name")
    return destination


def save_created_token(destination: Path, token: str) -> None:
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(token.strip() + "\n")


def _body_credentials(value: Any) -> list[str]:
    if isinstance(value, dict):
        found = [v for k, v in value.items() if k in {"secret", "basic_auth_password", "basic_auth_user", "password", "token"} and isinstance(v, str) and v]
        return found + [secret for v in value.values() for secret in _body_credentials(v)]
    if isinstance(value, list):
        return [secret for v in value for secret in _body_credentials(v)]
    return []


def attachment_byte_limit() -> int:
    try:
        value = int(get_setting("VIKUNJA_MAX_ATTACHMENT_BYTES") or 20971520)
    except (ValueError, TypeError):
        raise ValueError("VIKUNJA_MAX_ATTACHMENT_BYTES must be a positive integer") from None
    if value < 1:
        raise ValueError("VIKUNJA_MAX_ATTACHMENT_BYTES must be a positive integer")
    return value


def attachment_directory() -> Path:
    configured = get_setting("VIKUNJA_ATTACHMENT_DIR")
    if not configured:
        raise ValueError("VIKUNJA_ATTACHMENT_DIR is required for upload and download")
    directory = Path(str(configured)).expanduser().resolve()
    if not directory.is_dir() or directory.stat().st_mode & 0o077:
        raise ValueError("VIKUNJA_ATTACHMENT_DIR must exist with private permissions, such as 0700")
    return directory


def _new_output_path(directory: Path, output_name: str) -> Path:
    if not isinstance(output_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", output_name):
        raise ValueError("output_name must be a simple filename")
    path = directory / output_name
    if path.exists() or path.is_symlink():
        raise ValueError("Output file already exists; choose a new output_name")
    return path
