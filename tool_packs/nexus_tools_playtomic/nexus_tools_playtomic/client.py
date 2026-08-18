from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Iterable
import requests

API_BASE = "https://api.playtomic.io/v1"
SPORT_ID = "PADEL"
STOKE_COORDINATE = "52.995,-2.18"
STOKE_RADIUS_M = 50_000
NTFY_TOPIC = "https://ntfy.hackerman.guru/padel"

CONFIGURED_VENUE_UIDS = {
    "powerleague-stoke-trentham-lakes",
    "ace-padel-stoke",
    "ace-padel-milton",
    "the-padel-barn-@-round-meadows-farm",
}

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "playtomic-bot/0.1 (+local on-demand checker)",
}


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    r = requests.get(f"{API_BASE}{path}", params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def list_stoke_venues(include_unconfigured: bool = False) -> list[dict[str, Any]]:
    tenants = _get("/tenants", {"coordinate": STOKE_COORDINATE, "radius": STOKE_RADIUS_M, "sport_id": SPORT_ID})
    out = []
    for t in tenants:
        if include_unconfigured or t.get("tenant_uid") in CONFIGURED_VENUE_UIDS:
            out.append({
                "tenant_id": t.get("tenant_id"),
                "tenant_uid": t.get("tenant_uid"),
                "name": t.get("tenant_name"),
                "city": (t.get("address") or {}).get("city"),
                "address": (t.get("address") or {}).get("street"),
                "currency": t.get("default_currency"),
            })
    return out


def _normalise_clock(clock: str, *, default_seconds: str = "00") -> str:
    if len(clock) == 5:
        return f"{clock}:{default_seconds}"
    return clock


def _window(day: str, start_time: str | None, end_time: str | None) -> tuple[str, str]:
    start = _normalise_clock(start_time or "00:00:00")
    end = _normalise_clock(end_time or "23:59:59", default_seconds="59")
    return f"{day}T{start}", f"{day}T{end}"


def _clock_from_when(when: Any) -> str | None:
    text = str(when or "")
    if "T" not in text:
        return None
    return _normalise_clock(text.split("T", 1)[1][:8])


def get_availability(day: str, *, tenant_ids: list[str] | None = None, start_time: str | None = None, end_time: str | None = None, min_duration: int | None = None) -> list[dict[str, Any]]:
    venues = list_stoke_venues()
    if tenant_ids:
        venues = [v for v in venues if v["tenant_id"] in set(tenant_ids)]
    start_min, start_max = _window(day, start_time, end_time)
    min_clock, max_clock = start_min[-8:], start_max[-8:]
    results = []
    for venue in venues:
        rows = _get("/availability", {"tenant_id": venue["tenant_id"], "sport_id": SPORT_ID, "local_start_min": start_min, "local_start_max": start_max})
        slots = []
        seen = set()
        for resource in rows:
            for slot in resource.get("slots", []):
                if slot.get("start_time", "") < min_clock or slot.get("start_time", "") > max_clock:
                    continue
                if min_duration and int(slot.get("duration") or 0) < min_duration:
                    continue
                item = {"resource_id": resource.get("resource_id"), **slot}
                key = (item.get("resource_id"), item.get("start_time"), item.get("duration"), item.get("price"))
                if key not in seen:
                    slots.append(item); seen.add(key)
        results.append({"venue": venue, "date": day, "slots": sorted(slots, key=lambda s: s.get("start_time", ""))})
    return results


def get_open_matches(*, start_date: str | None = None, end_date: str | None = None, start_time: str | None = None, end_time: str | None = None, tenant_ids: list[str] | None = None) -> list[dict[str, Any]]:
    venues = list_stoke_venues()
    if tenant_ids:
        venues = [v for v in venues if v["tenant_id"] in set(tenant_ids)]
    out = []
    seen = set()
    for venue in venues:
        # Playtomic's default /matches page can stop before future app-visible
        # suggestions for a venue (e.g. Monday morning matches at Ace Stoke).
        # Ask for a larger page, then apply our date/status filters locally.
        matches = _get("/matches", {"coordinate": STOKE_COORDINATE, "radius": STOKE_RADIUS_M, "sport_id": SPORT_ID, "tenant_id": venue["tenant_id"], "size": 1000})
        for m in matches:
            when = m.get("start_date") or m.get("start") or m.get("local_start")
            if start_date and when and str(when)[:10] < start_date: continue
            if end_date and when and str(when)[:10] > end_date: continue
            clock = _clock_from_when(when)
            if start_time and clock and clock < _normalise_clock(start_time): continue
            if end_time and clock and clock > _normalise_clock(end_time, default_seconds="59"): continue
            players = sum(len(t.get("players", [])) for t in m.get("teams", []))
            max_players = int(m.get("max_players_per_team") or 2) * 2
            if players <= 0 or players >= max_players: continue
            if m.get("visibility") == "HIDDEN": continue
            if m.get("registration_status") != "OPEN": continue
            if m.get("status") in {"CANCELED", "PLAYED"}: continue
            if when and str(when) < datetime.now().strftime("%Y-%m-%dT%H:%M:%S"): continue
            mid = m.get("match_id")
            if mid in seen: continue
            seen.add(mid)
            out.append(m)
    return sorted(out, key=lambda m: m.get("start_date") or m.get("start") or m.get("local_start") or "")


def format_price(price: str) -> str:
    text = str(price or "")
    return text.replace(" GBP", "").replace("GBP", "").strip().join(["£", ""]) if "GBP" in text else text

def format_availability(results: list[dict[str, Any]]) -> str:
    lines = ["Playtomic padel availability"]
    for r in results:
        lines.append(f"\n*{r['venue']['name'].strip()}* — {r['date']}")
        if not r["slots"]:
            lines.append("  No slots found")
            continue
        grouped: dict[tuple[str, int, str], int] = {}
        for s in r["slots"]:
            key = (str(s.get("start_time", ""))[:5], int(s.get("duration") or 0), str(s.get("price") or ""))
            grouped[key] = grouped.get(key, 0) + 1
        for (start, duration, price), count in list(grouped.items())[:30]:
            marker = f" _x{count}_" if count > 1 else ""
            lines.append(f"  {start} for {duration}m — {format_price(price)}{marker}")
        if len(grouped) > 30:
            lines.append(f"  …and {len(grouped) - 30} more")
    return "\n".join(lines)


def notify(message: str, *, title: str = "Padel") -> dict[str, Any]:
    r = requests.post(NTFY_TOPIC, data=message.encode(), headers={"Title": title}, timeout=15)
    return {"status_code": r.status_code, "ok": r.ok, "text": r.text[:200]}
