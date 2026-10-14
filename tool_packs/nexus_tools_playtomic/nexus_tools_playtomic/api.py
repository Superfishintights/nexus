"""Read-only Nexus tools for Playtomic padel discovery around Stoke-on-Trent."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from nexus.tool_registry import register_tool
from .client import list_stoke_venues, get_availability, get_open_matches, format_availability, notify

@register_tool(namespace="playtomic", aliases=["venues", "stoke_venues", "padel_venues", "padel_courts", "local_padel"], description="List the configured Stoke-on-Trent Playtomic venues from the bot registry. include_unconfigured is retained for compatibility; geographic discovery is unavailable.", examples=['load_tool("playtomic.list_venues")()'])
def list_venues(include_unconfigured: bool = False) -> List[Dict[str, Any]]:
    return list_stoke_venues(include_unconfigured=include_unconfigured)

@register_tool(namespace="playtomic", aliases=["availability", "court_availability", "padel_availability", "padel_court_availability", "court_slots", "padel_slots", "booking_slots", "tonight_padel", "padel_tonight"], description="Get read-only Playtomic padel court availability and private booking slots for configured Stoke-on-Trent venues. Only when the user asks to create a public/open match, set include_open_match_links=True to add links to the club Open Matches tab with the requested date/time. Court slots and prices remain private booking references; public match availability, duration and price must be confirmed in Playtomic. Does not create, join or pay for a match.", examples=['load_tool("playtomic.get_court_availability")("2026-06-07", start_time="17:00")', 'load_tool("playtomic.get_court_availability")("2026-10-07", start_time="18:00", include_open_match_links=True)'])
def get_court_availability(day: str, *, tenant_ids: Optional[List[str]] = None, start_time: Optional[str] = None, end_time: Optional[str] = None, min_duration: Optional[int] = None, include_open_match_links: bool = False, send_ntfy: bool = False) -> Dict[str, Any]:
    results = get_availability(day, tenant_ids=tenant_ids, start_time=start_time, end_time=end_time, min_duration=min_duration, include_open_match_links=include_open_match_links)
    message = format_availability(results)
    payload: Dict[str, Any] = {"results": results, "summary": message}
    if send_ntfy:
        payload["notification"] = notify(message, title="Padel availability")
    return payload

@register_tool(namespace="playtomic", aliases=["matches", "open_matches", "padel_matches", "open_padel_matches", "padel_games", "padel_match_finder"], description="Get read-only open Playtomic padel matches, games, and player slots for configured Stoke-on-Trent venues. Currently unavailable through the website transport, matching the Playtomic bot; raises an explicit capability error. Date and local start-time parameters are retained for compatibility.", examples=['load_tool("playtomic.find_open_matches")(start_date="2026-06-07", end_date="2026-06-14")', 'load_tool("playtomic.find_open_matches")(start_date="2026-06-08", end_date="2026-06-08", end_time="11:00")'])
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


@register_tool(namespace="playtomic", description="Search publicly listed Playtomic academy classes and coaching sessions at configured local clubs within an inclusive date range of 1 to 14 days. Returns public-class listings and booking links, including any socials listed there; excludes private coach availability and full courses. Public listings may not cover every session. Times use Europe/London. Read-only; does not book or message anyone.", examples=['load_tool("playtomic.get_academy_sessions")(start_date="2026-09-22", end_date="2026-09-29")'])
def get_academy_sessions(*, start_date: str, end_date: str, start_time: Optional[str] = None, end_time: Optional[str] = None, tenant_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    from .client import get_academy_sessions as search
    results = search(start_date=start_date, end_date=end_date, start_time=start_time,
                     end_time=end_time, tenant_ids=tenant_ids)
    return {"results": results, "coverage": "Public academy class listings only; includes socials where published, excludes private coach calendars and full courses. Listings may not be exhaustive."}
