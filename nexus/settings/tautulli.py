from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class TautulliSettings:
    """Configuration required to interact with a Tautulli instance."""

    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "TautulliSettings":
        """Create settings by reading environment variables."""

        base_url = require_setting(
            "TAUTULLI_URL",
            message="Missing Tautulli URL. Set the TAUTULLI_URL environment variable.",
        )
        api_key = require_setting(
            "TAUTULLI_API_KEY",
            message="Missing Tautulli API key. Set the TAUTULLI_API_KEY environment variable.",
        )

        return cls(base_url=normalize_url(base_url), api_key=api_key)

