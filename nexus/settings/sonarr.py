from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class SonarrSettings:
    """Configuration required to interact with a Sonarr instance."""

    url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "SonarrSettings":
        """Create settings by reading environment variables."""

        url = require_setting(
            "SONARR_URL",
            message="Missing Sonarr URL. Set the SONARR_URL environment variable.",
        )
        api_key = require_setting(
            "SONARR_API_KEY",
            message="Missing Sonarr API Key. Set the SONARR_API_KEY environment variable.",
        )

        return cls(url=normalize_url(url), api_key=api_key)
