"""Shared Google API support for Nexus tool packs."""

from .client import (
    GoogleApiClient,
    GoogleApiError,
    GoogleAuthError,
    GoogleResponse,
    build_authorization_url,
    coerce_json,
    coerce_list,
    coerce_optional_bool,
    coerce_optional_int,
    coerce_optional_str,
    exchange_authorization_code,
    exchange_authorization_redirect,
    get_client,
    quote_path_segment,
    quote_resource_name,
    run_loopback_authorization,
)

__all__ = [
    "GoogleApiClient",
    "GoogleApiError",
    "GoogleAuthError",
    "GoogleResponse",
    "build_authorization_url",
    "coerce_json",
    "coerce_list",
    "coerce_optional_bool",
    "coerce_optional_int",
    "coerce_optional_str",
    "exchange_authorization_code",
    "exchange_authorization_redirect",
    "get_client",
    "quote_path_segment",
    "quote_resource_name",
    "run_loopback_authorization",
]
