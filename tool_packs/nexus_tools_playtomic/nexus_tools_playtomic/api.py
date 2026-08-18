"""Read-only Nexus tools for Playtomic padel discovery around Stoke-on-Trent."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from nexus.tool_registry import register_tool
from .client import list_stoke_venues, get_availability, get_open_matches, format_availability, notify

@register_tool(namespace="playtomic", aliases=["venues", "stoke_venues", "padel_venues", "padel_courts", "local_padel"], description="List configured Stoke-on-Trent Playtomic padel venues and courts for local padel discovery.", examples=['load_tool("playtomic.list_venues")()'])
def list_venues(include_unconfigured: bool = False) -> List[Dict[str, Any]]:
    return list_stoke_venues(include_unconfigured=include_unconfigured)

@register_tool(namespace="playtomic", aliases=["availability", "court_availability", "padel_availability", "padel_court_availability", "court_slots", "padel_slots", "booking_slots", "tonight_padel", "padel_tonight"], description="Get read-only Playtomic padel court availability / booking slots for configured Stoke-on-Trent venues; use for requests like finding padel courts tonight, from 5pm onwards, this evening, or after work.", examples=['load_tool("playtomic.get_court_availability")("2026-06-07", start_time="17:00")'])
def get_court_availability(day: str, *, tenant_ids: Optional[List[str]] = None, start_time: Optional[str] = None, end_time: Optional[str] = None, min_duration: Optional[int] = None, send_ntfy: bool = False) -> Dict[str, Any]:
    results = get_availability(day, tenant_ids=tenant_ids, start_time=start_time, end_time=end_time, min_duration=min_duration)
    message = format_availability(results)
    payload: Dict[str, Any] = {"results": results, "summary": message}
    if send_ntfy:
        payload["notification"] = notify(message, title="Padel availability")
    return payload

@register_tool(namespace="playtomic", aliases=["matches", "open_matches", "padel_matches", "open_padel_matches", "padel_games", "padel_match_finder"], description="Get read-only open Playtomic padel matches, games, and player slots for configured Stoke-on-Trent venues. Supports date and local start-time filters.", examples=['load_tool("playtomic.find_open_matches")(start_date="2026-06-07", end_date="2026-06-14")', 'load_tool("playtomic.find_open_matches")(start_date="2026-06-08", end_date="2026-06-08", end_time="11:00")'])
def find_open_matches(*, start_date: Optional[str] = None, end_date: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None, tenant_ids: Optional[List[str]] = None, send_ntfy: bool = False) -> Dict[str, Any]:
    matches = get_open_matches(start_date=start_date, end_date=end_date, start_time=start_time, end_time=end_time, tenant_ids=tenant_ids)
    summary = f"Found {len(matches)} Playtomic padel open matches"
    if start_date or end_date or start_time or end_time:
        summary += f" ({start_date or 'any'} to {end_date or 'any'}, {start_time or '00:00'} to {end_time or '23:59'})"
    payload: Dict[str, Any] = {"matches": matches, "summary": summary}
    if send_ntfy:
        lines = [summary] + [f"{m.get('start_date')} — {m.get('location')} — {m.get('price')}" for m in matches[:25]]
        payload["notification"] = notify("\n".join(lines), title="Padel open matches")
    return payload
