"""Typed errors for Starling tools."""

from __future__ import annotations

from typing import Any, Optional


class StarlingError(Exception):
    """Base error for Starling tool failures."""


class StarlingAuthError(StarlingError):
    """Authentication failure or missing auth configuration."""


class StarlingScopeError(StarlingError):
    """Token is present but lacks a required scope."""


class StarlingSigningError(StarlingError):
    """A signed endpoint could not be signed correctly."""


class StarlingMTLSError(StarlingError):
    """mTLS or custom CA configuration failed."""


class StarlingValidationError(StarlingError):
    """Input validation failed before making a request."""


class StarlingAPIError(StarlingError):
    """Starling API request failed."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        detail: Any = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        self.method = method
        self.endpoint = endpoint
