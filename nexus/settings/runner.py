from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..env import ConfigurationError
from .confluence import ConfluenceSettings
from .gitlab import GitLabSettings
from .jenkins import JenkinsSettings
from .jira import JiraSettings
from .sonarr import SonarrSettings
from .sourcegraph import SourcegraphSettings
from .talos import TalosSettings
from .tautulli import TautulliSettings


@dataclass(frozen=True)
class RunnerSettings:
    """Top-level settings for the runner environment."""

    jira: Optional[JiraSettings] = None
    sourcegraph: Optional[SourcegraphSettings] = None
    confluence: Optional[ConfluenceSettings] = None
    gitlab: Optional[GitLabSettings] = None
    jenkins: Optional[JenkinsSettings] = None
    sonarr: Optional[SonarrSettings] = None
    talos: Optional[TalosSettings] = None
    tautulli: Optional[TautulliSettings] = None

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
            sonarr = SonarrSettings.from_env()
        except ConfigurationError:
            sonarr = None

        try:
            talos = TalosSettings.from_env()
        except ConfigurationError:
            talos = None

        try:
            tautulli = TautulliSettings.from_env()
        except ConfigurationError:
            tautulli = None

        return cls(
            jira=jira,
            sourcegraph=sourcegraph,
            confluence=confluence,
            gitlab=gitlab,
            jenkins=jenkins,
            sonarr=sonarr,
            talos=talos,
            tautulli=tautulli,
        )

