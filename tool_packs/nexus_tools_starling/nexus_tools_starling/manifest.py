"""Starling endpoint metadata used by the shared client and curated tools."""

from __future__ import annotations

import re
from typing import Pattern

TOKEN_PROFILE_READ_EDIT = "read_edit"
TOKEN_PROFILE_PAYEE_SAVINGS_CREATE = "payee_savings_create"
TOKEN_PROFILE_PAYMENT_INITIATION = "payment_initiation"

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

TOKEN_PROFILE_PATTERNS: tuple[tuple[str, str, Pattern[str]], ...] = (
    (TOKEN_PROFILE_PAYEE_SAVINGS_CREATE, "PUT", re.compile(r"^payees$")),
    (TOKEN_PROFILE_PAYEE_SAVINGS_CREATE, "PUT", re.compile(r"^payees/[^/]+/account$")),
    (TOKEN_PROFILE_PAYEE_SAVINGS_CREATE, "PUT", re.compile(r"^feed/account/[^/]+/round-up$")),
    (TOKEN_PROFILE_PAYEE_SAVINGS_CREATE, "PUT", re.compile(r"^account/[^/]+/savings-goals$")),
    (
        TOKEN_PROFILE_PAYEE_SAVINGS_CREATE,
        "PUT",
        re.compile(r"^account/[^/]+/savings-goals/[^/]+$"),
    ),
    (
        TOKEN_PROFILE_PAYEE_SAVINGS_CREATE,
        "PUT",
        re.compile(r"^account/[^/]+/savings-goals/[^/]+/(add-money|withdraw-money)/[^/]+$"),
    ),
    (
        TOKEN_PROFILE_PAYEE_SAVINGS_CREATE,
        "PUT",
        re.compile(r"^account/[^/]+/savings-goals/[^/]+/recurring-transfer$"),
    ),
    (
        TOKEN_PROFILE_PAYMENT_INITIATION,
        "PUT",
        re.compile(r"^payments/local/account/[^/]+/category/[^/]+$"),
    ),
    (
        TOKEN_PROFILE_PAYMENT_INITIATION,
        "PUT",
        re.compile(r"^payments/local/account/[^/]+/category/[^/]+/standing-orders$"),
    ),
    (
        TOKEN_PROFILE_PAYMENT_INITIATION,
        "PUT",
        re.compile(r"^payments/local/account/[^/]+/category/[^/]+/standing-orders/[^/]+$"),
    ),
    (
        TOKEN_PROFILE_PAYMENT_INITIATION,
        "DELETE",
        re.compile(r"^payments/local/account/[^/]+/category/[^/]+/standing-orders/[^/]+$"),
    ),
)


def requires_signature(method: str, endpoint: str) -> bool:
    normalized_method = method.upper()
    normalized_endpoint = endpoint.strip("/")
    return any(
        candidate_method == normalized_method and pattern.match(normalized_endpoint)
        for candidate_method, pattern in SIGNED_OPERATION_PATTERNS
    )


def resolve_token_profile(method: str, endpoint: str) -> str:
    normalized_method = method.upper()
    normalized_endpoint = endpoint.strip("/")
    for profile, candidate_method, pattern in TOKEN_PROFILE_PATTERNS:
        if candidate_method == normalized_method and pattern.match(normalized_endpoint):
            return profile
    return TOKEN_PROFILE_READ_EDIT


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
