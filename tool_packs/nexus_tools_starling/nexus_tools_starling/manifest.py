"""Starling endpoint metadata used by the shared client and curated tools."""

from __future__ import annotations

import re
from typing import Pattern

SIGNED_OPERATION_PATTERNS: tuple[tuple[str, Pattern[str]], ...] = (
    ("PUT", re.compile(r"^account-holder/individual/email$")),
    ("POST", re.compile(r"^addresses$")),
    ("PUT", re.compile(r"^payments/local/account/[^/]+/category/[^/]+$")),
    ("PUT", re.compile(r"^payments/local/account/[^/]+/category/[^/]+/standing-orders$")),
    (
        "PUT",
        re.compile(r"^payments/local/account/[^/]+/category/[^/]+/standing-orders/[^/]+$"),
    ),
    (
        "DELETE",
        re.compile(r"^payments/local/account/[^/]+/category/[^/]+/standing-orders/[^/]+$"),
    ),
)

TEXT_RESPONSE_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"^accounts/[^/]+/feed-export$"),
)

BINARY_RESPONSE_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"^account-holder/[^/]+/profile-image$"),
    re.compile(r"^payees/[^/]+/image$"),
    re.compile(r"^feed/account/[^/]+/category/[^/]+/[^/]+/attachments/[^/]+$"),
)


def requires_signature(method: str, endpoint: str) -> bool:
    normalized_method = method.upper()
    normalized_endpoint = endpoint.strip("/")
    return any(
        candidate_method == normalized_method and pattern.match(normalized_endpoint)
        for candidate_method, pattern in SIGNED_OPERATION_PATTERNS
    )


def is_text_response(endpoint: str, content_type: str) -> bool:
    normalized_endpoint = endpoint.strip("/")
    if content_type.startswith("text/"):
        return True
    return any(pattern.match(normalized_endpoint) for pattern in TEXT_RESPONSE_PATTERNS)


def is_binary_response(endpoint: str, content_type: str) -> bool:
    normalized_endpoint = endpoint.strip("/")
    if content_type.startswith("image/") or content_type == "application/octet-stream":
        return True
    return any(pattern.match(normalized_endpoint) for pattern in BINARY_RESPONSE_PATTERNS)
