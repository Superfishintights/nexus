from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class ConfluenceSettings:
    """Configuration required to interact with a Confluence instance."""

    url: str
    pat: str

    @classmethod
    def from_env(cls) -> "ConfluenceSettings":
        """Create settings by reading environment variables."""

        url = require_setting(
            "CONFLUENCE_URL",
            message="Missing Confluence URL. Set the CONFLUENCE_URL environment variable.",
        )
        pat = require_setting(
            "CONFLUENCE_PAT",
            message="Missing Confluence PAT. Set the CONFLUENCE_PAT environment variable.",
        )

        return cls(url=normalize_url(url), pat=pat)

