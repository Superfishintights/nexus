"""Gmail-specific helpers layered on the shared Google client."""

from __future__ import annotations

import base64
from typing import Any, Dict, Iterable, List, Optional

from nexus_tools_google_common.client import (
    coerce_json,
    coerce_list,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    get_client,
    quote_path_segment,
)


def gmail_request(
    path: str,
    *,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Any] = None,
    binary: bool = False,
) -> Any:
    return get_client().request("gmail", path, method=method, params=params, payload=payload, binary=binary)


def user_path(user_id: str, suffix: str) -> str:
    return f"users/{quote_path_segment(user_id)}/{suffix.strip('/')}"


def decode_base64url(data: Optional[str]) -> bytes:
    if not data:
        return b""
    padded = data + ("=" * (-len(data) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def encode_base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def message_headers(message: Dict[str, Any]) -> Dict[str, str]:
    headers = (message.get("payload") or {}).get("headers") or []
    result: Dict[str, str] = {}
    for header in headers:
        name = str(header.get("name") or "")
        if name:
            result[name] = str(header.get("value") or "")
    return result


def iter_message_parts(payload: Optional[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    if not payload:
        return
    yield payload
    for part in payload.get("parts") or []:
        yield from iter_message_parts(part)


def extract_text_parts(message: Dict[str, Any]) -> Dict[str, Any]:
    plain: List[str] = []
    html: List[str] = []
    attachments: List[Dict[str, Any]] = []
    for part in iter_message_parts(message.get("payload")):
        mime_type = part.get("mimeType")
        body = part.get("body") or {}
        filename = part.get("filename") or ""
        if filename or body.get("attachmentId"):
            attachments.append(
                {
                    "filename": filename,
                    "mimeType": mime_type,
                    "attachmentId": body.get("attachmentId"),
                    "size": body.get("size"),
                    "partId": part.get("partId"),
                }
            )
            continue
        data = body.get("data")
        if not data:
            continue
        text = decode_base64url(str(data)).decode("utf-8", errors="replace")
        if mime_type == "text/plain":
            plain.append(text)
        elif mime_type == "text/html":
            html.append(text)
    return {
        "id": message.get("id"),
        "threadId": message.get("threadId"),
        "snippet": message.get("snippet"),
        "headers": message_headers(message),
        "textPlain": "\n".join(plain),
        "textHtml": "\n".join(html),
        "attachments": attachments,
    }
