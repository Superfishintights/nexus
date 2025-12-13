from __future__ import annotations

from dataclasses import dataclass

from ._helpers import normalize_url, require_setting


@dataclass(frozen=True)
class JenkinsSettings:
    """Configuration required to interact with a Jenkins instance."""

    url: str
    username: str
    token: str

    @classmethod
    def from_env(cls) -> "JenkinsSettings":
        """Create settings by reading environment variables."""

        url = require_setting(
            "JENKINS_URL",
            message="Missing Jenkins URL. Set the JENKINS_URL environment variable.",
        )
        username = require_setting(
            "JENKINS_USERNAME",
            message="Missing Jenkins username. Set the JENKINS_USERNAME environment variable.",
        )
        token = require_setting(
            "JENKINS_TOKEN",
            message="Missing Jenkins token. Set the JENKINS_TOKEN environment variable.",
        )

        return cls(url=normalize_url(url), username=username, token=token)

