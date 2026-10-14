from __future__ import annotations

from datetime import datetime, time as datetime_time, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import fcntl
import json
import os
from pathlib import Path
import re
import time
from typing import Any
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from .config import PlaytomicConfig

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "playtomic-bot/0.2 (+configurable club availability checker)",
}


class CapabilityUnavailableError(RuntimeError):
    """The selected transport cannot provide this lookup."""


def default_config() -> PlaytomicConfig:
    return PlaytomicConfig.from_env()


def _get(path: str, params: dict[str, Any] | None = None, *, config: PlaytomicConfig | None = None) -> Any:
    cfg = config or default_config()
    url = path if path.startswith("https://playtomic.com/api/clubs/") else f"{cfg.api_base}{path}"
    last_error: Exception | None = None
    for attempt in range(1, cfg.http_retries + 1):
        _pace_playtomic_request(cfg)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=cfg.http_timeout_seconds)
            if _retryable_status(r.status_code) and attempt < cfg.http_retries:
                time.sleep(_retry_delay(r, attempt))
                continue
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as exc:
            last_error = exc
            status_code = exc.response.status_code if exc.response is not None else None
            if not _retryable_status(status_code) or attempt >= cfg.http_retries:
                raise
            time.sleep(_retry_delay(exc.response, attempt))
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= cfg.http_retries:
                raise
            time.sleep(min(30, 2 ** (attempt - 1)))
    if last_error:
        raise last_error
    raise RuntimeError("Playtomic request failed")


def _pace_playtomic_request(cfg: PlaytomicConfig) -> None:
    interval = float(cfg.http_min_interval_seconds or 0)
    if interval <= 0:
        return
    state_path = Path(cfg.http_rate_state_file or os.path.join("/tmp", "playtomic-http-rate-limit.json"))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state_path.with_suffix(f"{state_path.suffix}.lock")
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        last_at = _read_last_request_at(state_path)
        wait_seconds = last_at + interval - time.time()
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        state_path.write_text(json.dumps({"last_request_at": time.time()}) + "\n", encoding="utf-8")


def _read_last_request_at(state_path: Path) -> float:
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return 0
    try:
        return float(payload.get("last_request_at") or 0)
    except (TypeError, ValueError):
        return 0


def _retryable_status(status_code: int | None) -> bool:
    return bool(status_code in {408, 429} or (status_code is not None and status_code >= 500))


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    retry_after = response.headers.get("retry-after") if response is not None else None
    if retry_after:
        try:
            return min(120, max(1, float(retry_after)))
        except ValueError:
            pass
    return min(30, 2 ** (attempt - 1))


def _cache_path(cfg: PlaytomicConfig) -> Path | None:
    if cfg.cache_file:
        return Path(cfg.cache_file)
    if cfg.http_rate_state_file:
        return Path(cfg.http_rate_state_file).with_name("playtomic-cache.json")
    return None


def _cache_get(cfg: PlaytomicConfig, key: str) -> Any | None:
    path = _cache_path(cfg)
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    item = payload.get(key) if isinstance(payload, dict) else None
    if not isinstance(item, dict):
        return None
    cached_at = item.get("cached_at")
    if not isinstance(cached_at, (int, float)):
        return None
    if cached_at + float(cfg.cache_ttl_seconds or 0) < time.time():
        return None
    return item.get("value")


def _cache_set(cfg: PlaytomicConfig, key: str, value: Any) -> None:
    path = _cache_path(cfg)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(f"{path.suffix}.lock")
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        payload[key] = {"cached_at": time.time(), "value": value}
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def list_venues(*, include_unconfigured: bool = False, config: PlaytomicConfig | None = None) -> list[dict[str, Any]]:
    cfg = config or default_config()
    tenants = _list_tenants(cfg)
    allowed = set(cfg.venue_uids)
    out = []
    for t in tenants:
        if include_unconfigured or not allowed or t.get("tenant_uid") in allowed:
            out.append({
                "tenant_id": t.get("tenant_id"),
                "tenant_uid": t.get("tenant_uid"),
                "slug": t.get("slug"),
                "name": t.get("tenant_name"),
                "city": (t.get("address") or {}).get("city"),
                "address": (t.get("address") or {}).get("street"),
                "currency": t.get("default_currency"),
                "aliases": t.get("aliases", []),
            })
    return out


def _list_tenants(cfg: PlaytomicConfig) -> list[dict[str, Any]]:
    if cfg.transport == "web":
        if not cfg.venue_registry:
            raise ValueError("PLAYTOMIC_VENUE_REGISTRY is required for web transport")
        tenants = json.loads(Path(cfg.venue_registry).read_text(encoding="utf-8"))
        if not isinstance(tenants, list) or any(not isinstance(t, dict) or not t.get("tenant_id") for t in tenants):
            raise ValueError("PLAYTOMIC_VENUE_REGISTRY must contain a list of venue objects with tenant_id")
        return tenants
    if cfg.transport != "legacy":
        raise ValueError("PLAYTOMIC_TRANSPORT must be legacy or web")
    key = f"tenants:{cfg.require_coordinate()}:{cfg.radius_m}:{cfg.sport_id}"
    cached = _cache_get(cfg, key)
    if isinstance(cached, list):
        return cached
    tenants = _get(
        "/tenants",
        {"coordinate": cfg.require_coordinate(), "radius": cfg.radius_m, "sport_id": cfg.sport_id},
        config=cfg,
    )
    if isinstance(tenants, list):
        _cache_set(cfg, key, tenants)
    return tenants


def _tenant_resources(tenant_id: str, cfg: PlaytomicConfig) -> list[dict[str, Any]]:
    if cfg.transport == "web":
        return next((t.get("resources", []) for t in _list_tenants(cfg) if str(t["tenant_id"]) == str(tenant_id)), [])
    key = f"tenant-resources:{tenant_id}:{cfg.sport_id}"
    cached = _cache_get(cfg, key)
    if isinstance(cached, list):
        return cached
    resources = _get(f"/tenants/{tenant_id}/resources", {"sport_id": cfg.sport_id}, config=cfg)
    if isinstance(resources, list):
        _cache_set(cfg, key, resources)
    return resources



def _normalise_clock(clock: str, *, default_seconds: str = "00") -> str:
    if len(clock) == 5:
        return f"{clock}:{default_seconds}"
    return clock


def _window(day: str, start_time: str | None, end_time: str | None) -> tuple[str, str]:
    start = _normalise_clock(start_time or "00:00:00")
    end = _normalise_clock(end_time or "23:59:59", default_seconds="59")
    return f"{day}T{start}", f"{day}T{end}"


def _api_window(day: str, start_time: str | None, end_time: str | None, cfg: PlaytomicConfig) -> tuple[str, str]:
    start, end = _window(day, start_time, end_time)
    tz = _configured_timezone(cfg)
    if tz is None:
        return start, end
    utc_start = _local_iso_to_utc_naive(start, tz)
    utc_end = _local_iso_to_utc_naive(end, tz)
    return min(start, utc_start), max(end, utc_end)


def _configured_timezone(cfg: PlaytomicConfig) -> ZoneInfo | None:
    if not cfg.timezone:
        return None
    try:
        return ZoneInfo(cfg.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid Playtomic timezone: {cfg.timezone}") from exc


def _local_iso_to_utc_naive(value: str, tz: ZoneInfo) -> str:
    local = datetime.fromisoformat(value).replace(tzinfo=tz)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _local_clock_from_api_clock(day: str, clock: str, cfg: PlaytomicConfig) -> str:
    tz = _configured_timezone(cfg)
    normalised = _normalise_clock(clock)
    if tz is None:
        return normalised
    utc_dt = datetime.combine(datetime.fromisoformat(day).date(), datetime_time.fromisoformat(normalised), tzinfo=timezone.utc)
    return utc_dt.astimezone(tz).strftime("%H:%M:%S")


def _clock_from_when(when: Any) -> str | None:
    text = str(when or "")
    if "T" not in text:
        return None
    return _normalise_clock(text.split("T", 1)[1][:8])


def get_availability(
    day: str,
    *,
    tenant_ids: list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    min_duration: int | None = None,
    court_format: str | None = None,
    include_open_match_links: bool = False,
    config: PlaytomicConfig | None = None,
) -> list[dict[str, Any]]:
    if type(include_open_match_links) is not bool:
        raise ValueError("include_open_match_links must be a boolean")
    cfg = config or default_config()
    if court_format not in (None, "any", "singles", "doubles"):
        raise ValueError("court_format must be singles, doubles, or any")
    venues = list_venues(config=cfg)
    if tenant_ids is not None:
        venues = [v for v in venues if v["tenant_id"] in set(tenant_ids)]
    if cfg.transport == "web":
        return _web_availability(day, venues, start_time, end_time, min_duration, cfg, court_format,
                                 include_open_match_links)
    start_min, start_max = _api_window(day, start_time, end_time, cfg)
    min_clock = _normalise_clock(start_time or "00:00:00")
    max_clock = _normalise_clock(end_time or "23:59:59", default_seconds="59")
    results_by_tenant = {
        str(venue["tenant_id"]): {"venue": venue, "date": day, "slots": []}
        for venue in venues
        if venue.get("tenant_id")
    }
    if not venues:
        return []
    resource_tenants = _resource_tenant_map(venues, cfg) if len(venues) > 1 else {}
    rows_by_tenant = _availability_rows_by_tenant(venues, resource_tenants, start_min, start_max, cfg)
    for venue in venues:
        rows = rows_by_tenant.get(str(venue["tenant_id"]), [])
        slots = []
        seen = set()
        for resource in rows:
            for slot in resource.get("slots", []):
                local_start_time = _local_clock_from_api_clock(day, str(slot.get("start_time", "")), cfg)
                if local_start_time < min_clock or local_start_time > max_clock:
                    continue
                if min_duration and int(slot.get("duration") or 0) < min_duration:
                    continue
                metadata = _court_metadata(resource)
                if court_format in ("singles", "doubles") and metadata["court_format"] != court_format:
                    continue
                item = {"resource_id": resource.get("resource_id"), **slot, **metadata, "start_time": local_start_time}
                key = (item.get("resource_id"), item.get("start_time"), item.get("duration"), item.get("price"))
                if key not in seen:
                    slots.append(item)
                    seen.add(key)
        results_by_tenant[str(venue["tenant_id"])]["slots"] = sorted(slots, key=lambda s: s.get("start_time", ""))
    return list(results_by_tenant.values())


def _court_metadata(resource: dict[str, Any]) -> dict[str, Any]:
    features = resource.get("features") or []
    # Only explicit upstream format metadata is evidence of court capacity.
    singles = "single" in features
    doubles = "double" in features
    court_format = "singles" if singles and not doubles else "doubles" if doubles and not singles else "unknown"
    return {"court_format": court_format, "player_count": {"singles": 2, "doubles": 4}.get(court_format)}


def _booking_url(tenant_id: Any, resource_id: Any, start: datetime, duration: Any) -> str | None:
    if not tenant_id or not resource_id or not duration:
        return None
    utc_start = start.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return "https://app.playtomic.com/payments?" + urlencode({
        "type": "CUSTOMER_MATCH", "tenant_id": tenant_id, "resource_id": resource_id,
        "start": utc_start, "duration": int(duration), "sport_id": "PADEL",
    })


def _open_match_url(tenant_id: Any, start: datetime, sport_id: str = "PADEL") -> str | None:
    """Open the club's public match selector at a time, without selecting a court or duration."""
    if not tenant_id:
        return None
    utc_start = start.astimezone(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    return f"https://app.playtomic.com/tenant/{quote(str(tenant_id), safe='')}/matches?" + urlencode({
        "sport_id": sport_id, "from_date": utc_start,
    })


def _shorten_booking_urls(results: list[dict[str, Any]]) -> None:
    """Shorten one lookup as a batch; direct links remain usable on any failure."""
    slots = [slot for result in results for slot in result["slots"]]
    targets = []
    for slot in slots:
        fields = [("booking_url", "direct_booking_url")]
        if "open_match_url" in slot or "direct_open_match_url" in slot:
            fields.append(("open_match_url", "direct_open_match_url"))
        for field, direct_field in fields:
            direct = slot.get(direct_field) or slot.get(field)
            slot[direct_field] = direct
            slot[field] = direct
            if isinstance(direct, str) and direct:
                targets.append((slot, field, direct))
    urls = list(dict.fromkeys(direct for _, _, direct in targets))
    api_url = os.environ.get("PADDY_LINKS_API_URL", "").strip().rstrip("/")
    key_file = os.environ.get("PADDY_LINKS_API_KEY_FILE", "").strip()
    if not urls or not api_url or not key_file:
        return
    try:
        key = Path(key_file).read_text(encoding="utf-8").strip()
        if not key:
            return
        response = requests.post(
            f"{api_url}/internal/shorten", json={"urls": urls},
            headers={"Authorization": f"Bearer {key}"}, timeout=3, allow_redirects=False,
        )
        response.raise_for_status()
        if not 200 <= response.status_code < 300:
            return
        payload = response.json()
    except (OSError, UnicodeError, requests.RequestException, ValueError):
        return
    links = payload.get("links") if isinstance(payload, dict) else None
    if not isinstance(links, dict):
        return
    for slot, field, direct in targets:
        short = links.get(direct)
        if isinstance(short, str) and re.fullmatch(r"https://paddy\.hackerman\.guru/b/[A-Za-z0-9_-]{10,12}", short):
            slot[field] = short


def _web_availability(day, venues, start_time, end_time, min_duration, cfg, court_format=None,
                      include_open_match_links=False):
    # The website selects the requested calendar date; returned resource dates
    # and slot clocks are UTC and must be converted together before filtering.
    tz = _configured_timezone(cfg) or timezone.utc
    min_clock = _normalise_clock(start_time or "00:00:00")
    max_clock = _normalise_clock(end_time or "23:59:59", default_seconds="59")
    results = []
    for venue in venues:
        rows = _get("https://playtomic.com/api/clubs/availability", {
            "tenant_id": venue["tenant_id"], "date": day, "sport_id": cfg.sport_id,
        }, config=cfg)
        if not isinstance(rows, list):
            raise ValueError("Unexpected Playtomic availability response")
        resources = {str(r.get("resource_id")): r for r in _tenant_resources(venue["tenant_id"], cfg)}
        slots, seen = [], set()
        for resource in rows:
            if not isinstance(resource, dict) or not isinstance(resource.get("slots"), list):
                raise ValueError("Unexpected Playtomic resource availability response")
            registry_resource = resources.get(str(resource.get("resource_id")), {})
            metadata = _court_metadata(registry_resource)
            if court_format in ("singles", "doubles") and metadata["court_format"] != court_format:
                continue
            for slot in resource["slots"]:
                utc_date = resource.get("start_date")
                if not utc_date:
                    raise ValueError("Playtomic availability resource is missing its UTC start_date")
                when = datetime.fromisoformat(f"{str(utc_date)[:10]}T{slot['start_time']}").replace(tzinfo=timezone.utc)
                local = when.astimezone(tz)
                clock = local.strftime("%H:%M:%S")
                if local.date().isoformat() != day or not min_clock <= clock <= max_clock:
                    continue
                if min_duration and int(slot.get("duration") or 0) < min_duration:
                    continue
                item = {**slot, **metadata, "resource_id": resource.get("resource_id"),
                        "resource_name": registry_resource.get("name"),
                        "start_time": clock, "start_date": local.date().isoformat(),
                        "booking_url": _booking_url(venue["tenant_id"], resource.get("resource_id"), when, slot.get("duration"))}
                if include_open_match_links:
                    item["open_match_url"] = _open_match_url(venue["tenant_id"], when, cfg.sport_id)
                key = (item["resource_id"], when.isoformat(), item.get("duration"), str(item.get("price")))
                if key not in seen:
                    seen.add(key)
                    slots.append(item)
        results.append({"venue": venue, "date": day, "slots": sorted(slots, key=lambda s: s["start_time"])})
    _shorten_booking_urls(results)
    return results


def _resource_tenant_map(venues: list[dict[str, Any]], cfg: PlaytomicConfig) -> dict[str, str]:
    resource_tenants: dict[str, str] = {}
    for venue in venues:
        tenant_id = str(venue.get("tenant_id") or "")
        if not tenant_id:
            continue
        for resource in _tenant_resources(tenant_id, cfg):
            resource_id = resource.get("resource_id")
            if resource_id:
                resource_tenants[str(resource_id)] = tenant_id
    return resource_tenants


def _availability_rows_by_tenant(
    venues: list[dict[str, Any]],
    resource_tenants: dict[str, str],
    start_min: str,
    start_max: str,
    cfg: PlaytomicConfig,
) -> dict[str, list[dict[str, Any]]]:
    tenant_ids = [str(venue["tenant_id"]) for venue in venues if venue.get("tenant_id")]
    if len(tenant_ids) <= 1:
        tenant_id = tenant_ids[0] if tenant_ids else ""
    else:
        tenant_id = ",".join(tenant_ids)
    rows = _get(
        "/availability",
        {"tenant_id": tenant_id, "sport_id": cfg.sport_id, "local_start_min": start_min, "local_start_max": start_max},
        config=cfg,
    )
    rows_by_tenant: dict[str, list[dict[str, Any]]] = {tenant_id: [] for tenant_id in tenant_ids}
    for row in rows:
        if len(tenant_ids) == 1:
            rows_by_tenant[tenant_ids[0]].append(row)
            continue
        owner = resource_tenants.get(str(row.get("resource_id") or ""))
        if owner in rows_by_tenant:
            rows_by_tenant[owner].append(row)
    return rows_by_tenant


def get_open_matches(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    tenant_ids: list[str] | None = None,
    config: PlaytomicConfig | None = None,
) -> list[dict[str, Any]]:
    cfg = config or default_config()
    if cfg.transport == "web":
        raise CapabilityUnavailableError("Open-match search is currently unavailable. Court availability can still be searched; please check the Playtomic app for open matches.")
    venues = list_venues(config=cfg)
    allowed_tenant_ids = {str(v["tenant_id"]) for v in venues if v.get("tenant_id")}
    if tenant_ids is not None:
        venues = [v for v in venues if v["tenant_id"] in set(tenant_ids)]
        allowed_tenant_ids = {str(v["tenant_id"]) for v in venues if v.get("tenant_id")}
    out = []
    seen = set()
    matches = _get_matches_for_venues(venues, cfg)
    for m in matches:
        match_tenant_id = _match_tenant_id(m)
        if allowed_tenant_ids and match_tenant_id not in allowed_tenant_ids:
            continue
        when = m.get("start_date") or m.get("start") or m.get("local_start")
        if start_date and when and str(when)[:10] < start_date:
            continue
        if end_date and when and str(when)[:10] > end_date:
            continue
        clock = _clock_from_when(when)
        if start_time and clock and clock < _normalise_clock(start_time):
            continue
        if end_time and clock and clock > _normalise_clock(end_time, default_seconds="59"):
            continue
        players = sum(len(t.get("players", [])) for t in m.get("teams", []))
        max_players = int(m.get("max_players_per_team") or 2) * 2
        if players <= 0 or players >= max_players:
            continue
        if m.get("visibility") == "HIDDEN":
            continue
        if m.get("registration_status") != "OPEN":
            continue
        if m.get("status") in {"CANCELED", "PLAYED"}:
            continue
        if when and str(when) < datetime.now().strftime("%Y-%m-%dT%H:%M:%S"):
            continue
        mid = m.get("match_id")
        if mid in seen:
            continue
        seen.add(mid)
        out.append(m)
    return sorted(out, key=lambda m: m.get("start_date") or m.get("start") or m.get("local_start") or "")


def _get_matches_for_venues(venues: list[dict[str, Any]], cfg: PlaytomicConfig) -> list[dict[str, Any]]:
    try:
        return _get(
            "/matches",
            {
                "coordinate": cfg.require_coordinate(),
                "radius": cfg.radius_m,
                "sport_id": cfg.sport_id,
                "size": 1000,
            },
            config=cfg,
        )
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code not in {400, 404}:
            raise
    matches: list[dict[str, Any]] = []
    for venue in venues:
        matches.extend(
            _get(
                "/matches",
                {
                    "coordinate": cfg.require_coordinate(),
                    "radius": cfg.radius_m,
                    "sport_id": cfg.sport_id,
                    "tenant_id": venue["tenant_id"],
                    "size": 1000,
                },
                config=cfg,
            )
        )
    return matches


def _match_tenant_id(match: dict[str, Any]) -> str | None:
    tenant = match.get("tenant") if isinstance(match.get("tenant"), dict) else {}
    location = match.get("location_info") if isinstance(match.get("location_info"), dict) else {}
    value = (
        match.get("tenant_id")
        or tenant.get("tenant_id")
        or tenant.get("id")
        or location.get("tenant_id")
        or location.get("id")
    )
    return str(value) if value else None


def format_price(price: str) -> str:
    text = str(price or "")
    return text.replace(" GBP", "").replace("GBP", "").strip().join(["£", ""]) if "GBP" in text else text


def _per_person_price(price: str, court_format: str) -> str:
    players = {"singles": 2, "doubles": 4}.get(court_format)
    if not players:
        return ""
    text = str(price).strip()
    symbols = {"GBP": "£", "EUR": "€", "USD": "$"}
    currency = next((code for code in symbols if text.endswith(" " + code)), None)
    if currency:
        amount = text[:-(len(currency) + 1)].strip()
    else:
        currency = next((code for code, symbol in symbols.items() if text.startswith(symbol)), None)
        amount = text[1:] if currency else ""
    if not currency:
        return ""
    try:
        total = Decimal(amount)
        if not total.is_finite() or total < 0:
            return ""
        share = (total / players).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return ""
    amount_text = f"{share:.0f}" if share == share.to_integral_value() else f"{share:.2f}"
    return f" ({symbols[currency]}{amount_text}pp)"


def format_availability(results: list[dict[str, Any]]) -> str:
    lines = ["Playtomic padel availability"]
    for r in results:
        lines.append(f"\n*{r['venue']['name'].strip()}* — {r['date']}")
        if not r["slots"]:
            lines.append("  No slots found")
            continue
        grouped: dict[tuple[str, int, str, str], int] = {}
        for s in r["slots"]:
            key = (str(s.get("start_time", ""))[:5], int(s.get("duration") or 0), str(s.get("price") if s.get("price") is not None else ""), str(s.get("court_format") or "unknown"))
            grouped[key] = grouped.get(key, 0) + 1
        lines.append("```")
        for (start, duration, price, court_format), count in list(grouped.items())[:30]:
            marker = f" x{count}" if count > 1 else ""
            label = {"singles": "Singles", "doubles": "Doubles"}.get(court_format, "Court format unknown")
            lines.append(f"{start} {duration:>3}m {label:<7} {format_price(price):>3}{_per_person_price(price, court_format)}{marker}")
        lines.append("```")
        if len(grouped) > 30:
            lines.append(f"  …and {len(grouped) - 30} more")
    return "\n".join(lines)


def format_matches(matches: list[dict[str, Any]], *, include_links: bool = True) -> str:
    if not matches:
        return "No Playtomic open matches found"
    lines = ["Playtomic open matches"]
    for match in matches[:30]:
        when = match.get("start_date") or match.get("start") or match.get("local_start")
        start = str(when).replace("T", " ")[:16] if when else "time unknown"
        tenant = match.get("tenant") if isinstance(match.get("tenant"), dict) else {}
        venue = (
            match.get("tenant_name")
            or match.get("venue_name")
            or tenant.get("name")
            or tenant.get("tenant_name")
        )
        teams = match.get("teams") if isinstance(match.get("teams"), list) else []
        players = sum(len(team.get("players", [])) for team in teams if isinstance(team, dict))
        try:
            max_players = int(match.get("max_players_per_team") or 2) * 2
        except (TypeError, ValueError):
            max_players = 0
        parts = [start]
        if venue:
            parts.append(str(venue))
        if max_players:
            parts.append(f"{players}/{max_players} players")
        if match.get("level"):
            parts.append(f"level {match['level']}")
        link = _match_link(match)
        if include_links and link:
            parts.append(str(link))
        lines.append("  " + " — ".join(parts))
    if len(matches) > 30:
        lines.append(f"  …and {len(matches) - 30} more")
    return "\n".join(lines)


def format_venues(venues: list[dict[str, Any]]) -> str:
    if not venues:
        return "No configured Playtomic venues found"
    lines = ["Configured Playtomic venues"]
    for venue in venues[:30]:
        parts = [str(venue.get("name") or venue.get("tenant_id") or "Unknown venue")]
        if venue.get("city"):
            parts.append(str(venue["city"]))
        if venue.get("address"):
            parts.append(str(venue["address"]))
        lines.append("  " + " — ".join(parts))
    if len(venues) > 30:
        lines.append(f"  …and {len(venues) - 30} more")
    return "\n".join(lines)


def _match_link(match: dict[str, Any]) -> str | None:
    for key in ("share_link", "web_url", "url", "link"):
        value = match.get(key)
        if value:
            return str(value)
    match_id = match.get("match_id")
    if match_id:
        return (
            f"https://app.playtomic.io/matches/{match_id}"
            "?utm_campaign=share&utm_medium=share_externally&product_type=open_match&utm_source=whatsapp_bot"
        )
    return None


def notify(message: str, *, title: str = "Padel", config: PlaytomicConfig | None = None) -> dict[str, Any]:
    cfg = config or default_config()
    if not cfg.ntfy_topic:
        raise ValueError("PLAYTOMIC_NTFY_TOPIC is required to send notifications")
    r = requests.post(cfg.ntfy_topic, data=message.encode(), headers={"Title": title}, timeout=15)
    return {"status_code": r.status_code, "ok": r.ok, "text": r.text[:200]}
