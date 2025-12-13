from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ._helpers import normalize_url, optional_setting, require_setting


@dataclass(frozen=True)
class SourcegraphSettings:
    """Configuration required to interact with a Sourcegraph instance."""

    host: str
    pat: str
    sgs_cookie: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SourcegraphSettings":
        """Create settings by reading environment variables.

        Reads from SOURCEGRAPH_HOST, SOURCEGRAPH_PAT/SOURCEGRAPH_TOKEN/X_PAT,
        and optionally SOURCEGRAPH_SGS_COOKIE (for deployments that require it).
        """

        host = require_setting(
            "SOURCEGRAPH_HOST",
            message="Missing Sourcegraph host. Set SOURCEGRAPH_HOST environment variable.",
        )
        pat = require_setting(
            "SOURCEGRAPH_PAT",
            "SOURCEGRAPH_TOKEN",
            "X_PAT",
            message=(
                "Missing Sourcegraph PAT. Set SOURCEGRAPH_PAT, SOURCEGRAPH_TOKEN, "
                "or X_PAT environment variable."
            ),
        )
        sgs_cookie = optional_setting("SOURCEGRAPH_SGS_COOKIE")

        return cls(host=normalize_url(host), pat=pat, sgs_cookie=sgs_cookie)

