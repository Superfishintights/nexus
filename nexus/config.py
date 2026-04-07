"""Public configuration surface for Nexus (backwards compatible).

Core Nexus configuration now lives in:
- `nexus/env.py` for env + `.env` handling
- `nexus/settings/runner.py` for core runner metadata

Pack-specific typed settings are no longer imported by core automatically.
"""

from __future__ import annotations

from .env import ConfigurationError, get_setting
from .settings.runner import RunnerSettings

__all__ = [
    "ConfigurationError",
    "RunnerSettings",
    "get_setting",
]
