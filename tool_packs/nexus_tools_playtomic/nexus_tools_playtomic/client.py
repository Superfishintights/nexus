"""Compatibility adapter using the deployed WhatsApp bot's website transport."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import requests
from ._bot import client as bot
from ._bot.config import PlaytomicConfig

NTFY_TOPIC_ENV = "PLAYTOMIC_NTFY_TOPIC"

def _config() -> PlaytomicConfig:
    return PlaytomicConfig(
        transport="web",
        venue_registry=os.getenv("PLAYTOMIC_VENUE_REGISTRY") or str(Path(__file__).with_name("venues.json")),
        timezone="Europe/London",
        http_retries=3,
        http_timeout_seconds=20,
    )

def list_stoke_venues(include_unconfigured: bool = False) -> list[dict[str, Any]]:
    # Website transport has a curated registry, not geographic discovery.
    return bot.list_venues(include_unconfigured=include_unconfigured, config=_config())

def get_availability(day: str, *, tenant_ids: list[str] | None = None, start_time: str | None = None, end_time: str | None = None, min_duration: int | None = None, include_open_match_links: bool = False) -> list[dict[str, Any]]:
    cfg = _config()
    if tenant_ids:
        known = {v["tenant_id"] for v in bot.list_venues(config=cfg)}
        unknown = set(tenant_ids) - known
        if unknown:
            raise ValueError("Unknown configured Playtomic tenant IDs: " + ", ".join(sorted(unknown)))
    # Preserve the existing empty-list meaning: all configured clubs.
    return bot.get_availability(day, tenant_ids=tenant_ids or None, start_time=start_time,
                                end_time=end_time, min_duration=min_duration, include_open_match_links=include_open_match_links, config=cfg)

def get_open_matches(*, start_date: str | None = None, end_date: str | None = None, start_time: str | None = None, end_time: str | None = None, tenant_ids: list[str] | None = None) -> list[dict[str, Any]]:
    return bot.get_open_matches(start_date=start_date, end_date=end_date,
                                start_time=start_time, end_time=end_time,
                                tenant_ids=tenant_ids, config=_config())


def format_price(price: str) -> str:
    text = str(price or "")
    return text.replace(" GBP", "").replace("GBP", "").strip().join(["£", ""]) if "GBP" in text else text

def format_availability(results: list[dict[str, Any]]) -> str:
    lines = ["Playtomic padel availability"]
    if any(slot.get("open_match_url") for result in results for slot in result["slots"]):
        lines.append("Open match links open the club's Open Matches tab at the requested time. "
                     "Court slots and prices below are private booking references. "
                     "Confirm public match availability, duration and price in Playtomic.")
    for r in results:
        lines.append(f"\n*{r['venue']['name'].strip()}* — {r['date']}")
        if not r["slots"]:
            lines.append("  No slots found")
            continue
        grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
        for s in r["slots"]:
            key = (str(s.get("start_time", ""))[:5], int(s.get("duration") or 0), str(s.get("price") or ""))
            grouped.setdefault(key, []).append(s)
        shown_open_urls: set[str] = set()
        for (start, duration, price), slots in list(grouped.items())[:30]:
            count = len(slots)
            marker = f" _x{count}_" if count > 1 else ""
            lines.append(f"  {start} for {duration}m — {format_price(price)}{marker}")
            for slot in slots:
                url = slot.get("booking_url")
                if url:
                    court = slot.get("resource_name") or f"Court {slot.get('resource_id') or 'unknown'}"
                    lines.append(f"Book {court}: {url}")
            for slot in slots:
                open_url = slot.get("open_match_url")
                if open_url and open_url not in shown_open_urls:
                    shown_open_urls.add(open_url)
                    lines.append(f"Open match options: {open_url}")
        if len(grouped) > 30:
            lines.append(f"  …and {len(grouped) - 30} more")
    return "\n".join(lines)


def notify(message: str, *, title: str = "Padel") -> dict[str, Any]:
    topic = os.getenv(NTFY_TOPIC_ENV, "").strip()
    if not topic:
        raise ValueError("PLAYTOMIC_NTFY_TOPIC is required for notifications")
    r = requests.post(topic, data=message.encode(), headers={"Title": title}, timeout=15)
    return {"status_code": r.status_code, "ok": r.ok, "text": r.text[:200]}


def get_academy_sessions(*, start_date: str, end_date: str, start_time: str | None = None, end_time: str | None = None, tenant_ids: list[str] | None = None) -> list[dict[str, Any]]:
    from ._bot.academy import get_academy_sessions as search
    cfg = _config()
    if tenant_ids:
        known = {v['tenant_id'] for v in bot.list_venues(config=cfg)}
        unknown = set(tenant_ids) - known
        if unknown:
            raise ValueError('Unknown configured Playtomic tenant IDs: ' + ', '.join(sorted(unknown)))
    return search(start_date=start_date, end_date=end_date, start_time=start_time,
                  end_time=end_time, tenant_ids=tenant_ids or None, config=cfg)
