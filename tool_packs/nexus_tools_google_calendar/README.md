# Nexus Google Calendar Tool Pack

Google Calendar v3 tools for Nexus under the `google_calendar` namespace.

This pack depends on `nexus-tools-google-common>=0.1.0` for Google OAuth and
HTTP transport. Tools intentionally return the raw Google Calendar JSON payload
so callers can preserve pagination cursors, sync tokens, ETags, and resource
fields that are not modeled locally.

## Coverage

- Calendars
- Calendar list entries
- Events and recurring event instances
- ACL rules
- Settings
- Colors
- Free/busy query
- Push notification channels

## Examples

```python
load_tool("google_calendar.list_events")("primary", max_results=10)
load_tool("google_calendar.insert_event")("primary", {"summary": "Standup", "start": {"dateTime": "2026-07-30T09:00:00Z"}, "end": {"dateTime": "2026-07-30T09:30:00Z"}})
load_tool("google_calendar.query_freebusy")({"timeMin": "2026-07-30T09:00:00Z", "timeMax": "2026-07-30T17:00:00Z", "items": [{"id": "primary"}]})
```
