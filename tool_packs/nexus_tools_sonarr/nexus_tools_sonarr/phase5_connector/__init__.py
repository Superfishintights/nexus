"""Phase 5 native connector contract for the Sonarr integration."""

from .adapter import (
    PersistentSonarrClient,
    SonarrConnectorAdapter,
    SonarrConnectorError,
    create_connector,
    create_registry,
)
from .source import load_source

__all__ = [
    "SonarrConnectorAdapter",
    "SonarrConnectorError",
    "PersistentSonarrClient",
    "create_connector",
    "create_registry",
    "load_source",
]
