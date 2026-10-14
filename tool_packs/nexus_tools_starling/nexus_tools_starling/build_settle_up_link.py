"""Build an amount-specific link only after a fresh public-page check."""

from datetime import datetime, timezone
from nexus.tool_registry import register_tool
from .settle_up_client import request_link


@register_tool(
    namespace="starling",
    description="Build and live-check a GBP Settle Up payment request link using the configured app-generated profile. Does not send a message or make a payment. If verification fails, obtain a fresh app link.",
    examples=['load_tool("starling.build_settle_up_link")(amount_minor_units=3593)'],
    aliases=[],
)
def build_settle_up_link(amount_minor_units: int) -> dict:
    """The check confirms the current recipient and amount URL, not payment completion or indefinite validity."""
    url, recipient, amount = request_link(amount_minor_units)
    return {
        "url": url,
        "recipient": recipient,
        "currency": "GBP",
        "amount": amount,
        "amount_minor_units": amount_minor_units,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "verification": "Public recipient page and payment URL verified. Payment completion and link lifetime are not guaranteed.",
    }
