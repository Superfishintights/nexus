from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
from typing import Iterable


DEFAULT_API_BASE = "https://api.playtomic.io/v1"
DEFAULT_SPORT_ID = "PADEL"


@dataclass(frozen=True)
class PlaytomicConfig:
    """Runtime configuration for one club/community deployment."""

    transport: str = "legacy"
    venue_registry: str | None = None
    api_base: str = DEFAULT_API_BASE
    sport_id: str = DEFAULT_SPORT_ID
    coordinate: str | None = None
    radius_m: int = 50_000
    venue_uids: tuple[str, ...] = ()
    ntfy_topic: str | None = None
    http_min_interval_seconds: float = 0
    http_rate_state_file: str | None = None
    http_retries: int = 3
    http_timeout_seconds: float = 20
    timezone: str | None = None
    cache_file: str | None = None
    cache_ttl_seconds: float = 7 * 24 * 60 * 60

    @classmethod
    def from_env(cls) -> "PlaytomicConfig":
        return cls(
            transport=os.getenv("PLAYTOMIC_TRANSPORT", "legacy"),
            venue_registry=_empty_to_none(os.getenv("PLAYTOMIC_VENUE_REGISTRY")),
            api_base=os.getenv("PLAYTOMIC_API_BASE", DEFAULT_API_BASE),
            sport_id=os.getenv("PLAYTOMIC_SPORT_ID", DEFAULT_SPORT_ID),
            coordinate=_empty_to_none(os.getenv("PLAYTOMIC_COORDINATE")),
            radius_m=int(os.getenv("PLAYTOMIC_RADIUS_M", "50000")),
            venue_uids=tuple(_split_csv(os.getenv("PLAYTOMIC_VENUE_UIDS", ""))),
            ntfy_topic=_empty_to_none(os.getenv("PLAYTOMIC_NTFY_TOPIC")),
            http_min_interval_seconds=float(os.getenv("PLAYTOMIC_HTTP_MIN_INTERVAL_SECONDS", "0")),
            http_rate_state_file=_empty_to_none(os.getenv("PLAYTOMIC_HTTP_RATE_STATE_FILE")),
            http_retries=max(1, int(os.getenv("PLAYTOMIC_HTTP_RETRIES", "3"))),
            http_timeout_seconds=float(os.getenv("PLAYTOMIC_HTTP_TIMEOUT_SECONDS", "20")),
            timezone=_empty_to_none(
                os.getenv("PLAYTOMIC_TIMEZONE")
                or os.getenv("WA_PI_WORKER_TIMEZONE")
                or os.getenv("TZ")
            ),
            cache_file=_empty_to_none(os.getenv("PLAYTOMIC_CACHE_FILE")),
            cache_ttl_seconds=float(os.getenv("PLAYTOMIC_CACHE_TTL_SECONDS", str(7 * 24 * 60 * 60))),
        )

    def with_overrides(
        self,
        *,
        coordinate: str | None = None,
        radius_m: int | None = None,
        venue_uids: Iterable[str] | None = None,
        ntfy_topic: str | None = None,
    ) -> "PlaytomicConfig":
        updates: dict[str, object] = {}
        if coordinate is not None:
            updates["coordinate"] = coordinate
        if radius_m is not None:
            updates["radius_m"] = radius_m
        if venue_uids is not None:
            updates["venue_uids"] = tuple(v for v in venue_uids if v)
        if ntfy_topic is not None:
            updates["ntfy_topic"] = ntfy_topic
        return replace(self, **updates)

    def require_coordinate(self) -> str:
        if not self.coordinate:
            raise ValueError(
                "PLAYTOMIC_COORDINATE is required (format: 'lat,lng'). "
                "Run `playtomic-bot init` or pass --coordinate."
            )
        return self.coordinate


def load_env_file(path: str | os.PathLike[str] | None) -> None:
    """Tiny .env loader so deployments do not need python-dotenv."""
    if not path:
        return
    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f"Config file not found: {env_path}")
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
