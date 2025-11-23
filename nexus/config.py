"""Configuration helpers for the nexus runner."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing."""


@dataclass(frozen=True)
class JiraSettings:
    """Configuration required to interact with a Jira instance."""

    hostname: str
    pat: str

    @classmethod
    def from_env(cls, *, hostname_var: str = "JIRA_HOSTNAME", pat_var: str = "JIRA_PAT") -> "JiraSettings":
        """Create settings by reading environment variables.

        Parameters
        ----------
        hostname_var:
            Environment variable holding the Jira hostname/URL.
        pat_var:
            Environment variable holding the Jira Personal Access Token.
        """

        hostname = os.getenv(hostname_var) or os.getenv(hostname_var.lower())
        pat = os.getenv(pat_var) or os.getenv(pat_var.lower())
        if not hostname:
            raise ConfigurationError(
                f"Missing Jira hostname. Set the `{hostname_var}` environment variable."
            )
        if not pat:
            raise ConfigurationError(
                f"Missing Jira PAT. Set the `{pat_var}` environment variable."
            )

        if not hostname.startswith(('http://', 'https://')):
            hostname = f"https://{hostname}"

        return cls(hostname=hostname.rstrip("/"), pat=pat)


@dataclass(frozen=True)
class SourcegraphSettings:
    """Configuration required to interact with a Sourcegraph instance."""

    host: str
    pat: str
    sgs_cookie: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SourcegraphSettings":
        """Create settings by reading environment variables.

        Reads from SOURCEGRAPH_HOST (default: sourcegraph.ab1.op.lb.local),
        SOURCEGRAPH_PAT/SOURCEGRAPH_TOKEN/X_PAT,
        and optionally SOURCEGRAPH_SGS_COOKIE for Deepsearch.
        """
        host = os.getenv("SOURCEGRAPH_HOST", "sourcegraph.ab1.op.lb.local")
        pat = (
            os.getenv("SOURCEGRAPH_PAT")
            or os.getenv("SOURCEGRAPH_TOKEN")
            or os.getenv("X_PAT")
        )
        sgs_cookie = os.getenv("SOURCEGRAPH_SGS_COOKIE")

        if not pat:
            raise ConfigurationError(
                "Missing Sourcegraph PAT. Set SOURCEGRAPH_PAT, SOURCEGRAPH_TOKEN, or X_PAT environment variable."
            )

        if not host.startswith(('http://', 'https://')):
            host = f"https://{host}"

        return cls(host=host.rstrip("/"), pat=pat, sgs_cookie=sgs_cookie)


@dataclass(frozen=True)
class ConfluenceSettings:
    """Configuration required to interact with a Confluence instance."""

    url: str
    pat: str

    @classmethod
    def from_env(cls) -> "ConfluenceSettings":
        """Create settings by reading environment variables.

        Reads from CONFLUENCE_URL and CONFLUENCE_PAT.
        """
        url = os.getenv("CONFLUENCE_URL")
        pat = os.getenv("CONFLUENCE_PAT")

        if not url:
            raise ConfigurationError(
                "Missing Confluence URL. Set the CONFLUENCE_URL environment variable."
            )
        if not pat:
            raise ConfigurationError(
                "Missing Confluence PAT. Set the CONFLUENCE_PAT environment variable."
            )

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        return cls(url=url.rstrip("/"), pat=pat)


@dataclass(frozen=True)
class GitLabSettings:
    """Configuration required to interact with a GitLab instance."""

    url: str
    token: str

    @classmethod
    def from_env(cls) -> "GitLabSettings":
        """Create settings by reading environment variables.

        Reads from GITLAB_URL and GITLAB_TOKEN.
        """
        url = os.getenv("GITLAB_URL")
        token = os.getenv("GITLAB_TOKEN")

        if not url:
            raise ConfigurationError(
                "Missing GitLab URL. Set the GITLAB_URL environment variable."
            )
        if not token:
            raise ConfigurationError(
                "Missing GitLab token. Set the GITLAB_TOKEN environment variable."
            )

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        return cls(url=url.rstrip("/"), token=token)


@dataclass(frozen=True)
class JenkinsSettings:
    """Configuration required to interact with a Jenkins instance."""

    url: str
    username: str
    token: str

    @classmethod
    def from_env(cls) -> "JenkinsSettings":
        """Create settings by reading environment variables.

        Reads from JENKINS_URL, JENKINS_USERNAME, and JENKINS_TOKEN.
        """
        url = os.getenv("JENKINS_URL")
        username = os.getenv("JENKINS_USERNAME")
        token = os.getenv("JENKINS_TOKEN")

        if not url:
            raise ConfigurationError(
                "Missing Jenkins URL. Set the JENKINS_URL environment variable."
            )
        if not username:
            raise ConfigurationError(
                "Missing Jenkins username. Set the JENKINS_USERNAME environment variable."
            )
        if not token:
            raise ConfigurationError(
                "Missing Jenkins token. Set the JENKINS_TOKEN environment variable."
            )

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        return cls(url=url.rstrip("/"), username=username, token=token)


@dataclass(frozen=True)
class TalosSettings:
    """Configuration required to interact with a Talos instance."""

    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> "TalosSettings":
        """Create settings by reading environment variables.

        Reads from TALOS_URL and TALOS_API_KEY.
        """
        base_url = os.getenv("TALOS_URL")
        api_key = os.getenv("TALOS_API_KEY")

        if not base_url:
            raise ConfigurationError(
                "Missing Talos URL. Set the TALOS_URL environment variable."
            )
        if not api_key:
            raise ConfigurationError(
                "Missing Talos API key. Set the TALOS_API_KEY environment variable."
            )

        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"

        return cls(base_url=base_url.rstrip("/"), api_key=api_key)


@dataclass(frozen=True)
class RunnerSettings:
    """Top-level settings for the runner environment."""

    jira: Optional[JiraSettings] = None
    sourcegraph: Optional[SourcegraphSettings] = None
    confluence: Optional[ConfluenceSettings] = None
    gitlab: Optional[GitLabSettings] = None
    jenkins: Optional[JenkinsSettings] = None
    talos: Optional[TalosSettings] = None

    @classmethod
    def from_env(cls) -> "RunnerSettings":
        try:
            jira = JiraSettings.from_env()
        except ConfigurationError:
            jira = None

        try:
            sourcegraph = SourcegraphSettings.from_env()
        except ConfigurationError:
            sourcegraph = None

        try:
            confluence = ConfluenceSettings.from_env()
        except ConfigurationError:
            confluence = None

        try:
            gitlab = GitLabSettings.from_env()
        except ConfigurationError:
            gitlab = None

        try:
            jenkins = JenkinsSettings.from_env()
        except ConfigurationError:
            jenkins = None

        try:
            talos = TalosSettings.from_env()
        except ConfigurationError:
            talos = None

        return cls(jira=jira, sourcegraph=sourcegraph, confluence=confluence, gitlab=gitlab, jenkins=jenkins, talos=talos)
