"""MIME composition helpers for Gmail raw message payloads."""

from __future__ import annotations

import base64
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .client import coerce_json, encode_base64url


def build_raw_message(
    *,
    to: str,
    subject: str,
    body: str,
    from_address: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
    headers: Optional[Any] = None,
    attachments: Optional[Any] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> str:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if from_address:
        msg["From"] = from_address
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    custom_headers = coerce_json(headers)
    if custom_headers:
        if not isinstance(custom_headers, dict):
            raise ValueError("headers must be a JSON object")
        for key, value in custom_headers.items():
            msg[str(key)] = str(value)
    if html:
        msg.add_alternative(body or "", subtype="html")
    else:
        msg.set_content(body or "")
    for item in _coerce_attachments(attachments):
        data, filename, content_type = _attachment_payload(item)
        maintype, subtype = content_type.split("/", 1) if "/" in content_type else ("application", "octet-stream")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    return encode_base64url(msg.as_bytes())


def _coerce_attachments(value: Optional[Any]) -> Iterable[Dict[str, Any]]:
    parsed = coerce_json(value)
    if parsed is None:
        return []
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    raise ValueError("attachments must be an object or array")


def _attachment_payload(item: Dict[str, Any]) -> tuple[bytes, str, str]:
    if not isinstance(item, dict):
        raise ValueError("each attachment must be an object")
    filename = str(item.get("filename") or item.get("name") or "attachment")
    content_type = str(item.get("contentType") or mimetypes.guess_type(filename)[0] or "application/octet-stream")
    if item.get("path"):
        data = Path(str(item["path"])).expanduser().read_bytes()
        return data, filename, content_type
    if item.get("contentBase64"):
        return base64.b64decode(str(item["contentBase64"])), filename, content_type
    if item.get("content"):
        return str(item["content"]).encode("utf-8"), filename, content_type
    raise ValueError("attachment requires path, contentBase64, or content")
