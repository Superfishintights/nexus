"""NZBGet pause and speed-limit tools."""

from __future__ import annotations

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="Set NZBGet download speed limit in KiB/s; this changes active download throttling.",
    examples=['load_tool("nzbget.rate")(1024)'],
    aliases=[],
)
def rate(limit: int) -> bool:
    """RPC signature: bool rate(int Limit)."""
    return get_client().call("rate", [limit])


@register_tool(
    namespace="nzbget",
    description="Pause the NZBGet download queue; active downloads will stop until resumed.",
    examples=['load_tool("nzbget.pausedownload")()'],
    aliases=[],
)
def pausedownload() -> bool:
    """RPC signature: bool pausedownload()."""
    return get_client().call("pausedownload")


@register_tool(
    namespace="nzbget",
    description="Resume the NZBGet download queue after it was paused.",
    examples=['load_tool("nzbget.resumedownload")()'],
    aliases=[],
)
def resumedownload() -> bool:
    """RPC signature: bool resumedownload()."""
    return get_client().call("resumedownload")


@register_tool(
    namespace="nzbget",
    description="Pause NZBGet post-processing; completed downloads may wait until post-processing is resumed.",
    examples=['load_tool("nzbget.pausepost")()'],
    aliases=[],
)
def pausepost() -> bool:
    """RPC signature: bool pausepost()."""
    return get_client().call("pausepost")


@register_tool(
    namespace="nzbget",
    description="Resume NZBGet post-processing after it was paused.",
    examples=['load_tool("nzbget.resumepost")()'],
    aliases=[],
)
def resumepost() -> bool:
    """RPC signature: bool resumepost()."""
    return get_client().call("resumepost")


@register_tool(
    namespace="nzbget",
    description="Pause scanning of NZBGet's incoming NZB directory.",
    examples=['load_tool("nzbget.pausescan")()'],
    aliases=[],
)
def pausescan() -> bool:
    """RPC signature: bool pausescan()."""
    return get_client().call("pausescan")


@register_tool(
    namespace="nzbget",
    description="Resume scanning of NZBGet's incoming NZB directory after it was paused.",
    examples=['load_tool("nzbget.resumescan")()'],
    aliases=[],
)
def resumescan() -> bool:
    """RPC signature: bool resumescan()."""
    return get_client().call("resumescan")


@register_tool(
    namespace="nzbget",
    description="Schedule NZBGet to resume all paused activities after a wait interval in seconds.",
    examples=['load_tool("nzbget.scheduleresume")(600)'],
    aliases=[],
)
def scheduleresume(seconds: int) -> bool:
    """RPC signature: bool scheduleresume(int Seconds)."""
    return get_client().call("scheduleresume", [seconds])
