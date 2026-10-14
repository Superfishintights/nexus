"""Unauthenticated public Settle Up checks, separate from bank API credentials."""

import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from nexus.config import get_setting
from .errors import StarlingValidationError


class RequestPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.recipient = ""
        self.links = []
        self.in_recipient = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "span" and "landing-page__intro--purple" in attrs.get("class", "").split():
            self.in_recipient = True
        if tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "span":
            self.in_recipient = False

    def handle_data(self, data):
        if self.in_recipient:
            self.recipient += data


def request_link(amount_minor_units):
    if type(amount_minor_units) is not int or amount_minor_units < 100:
        raise StarlingValidationError("amount_minor_units must be an integer of at least 100, meaning GBP 1.00")
    config_path = get_setting("STARLING_SETTLE_UP_CONFIG_FILE") or "/run/nexus-state/starling-settle-up.json"
    config = json.loads(Path(config_path).read_text())
    base = urlsplit(config["base_url"])
    expected = config["recipient_name"].strip()
    if (base.scheme != "https" or base.netloc != "settleup.starlingbank.com"
            or not re.fullmatch(r"/[A-Za-z0-9_-]+", base.path)
            or base.query or base.fragment or not expected):
        raise StarlingValidationError("Settle Up config needs a bare HTTPS Starling profile URL and recipient_name")
    amount = f"{amount_minor_units // 100}.{amount_minor_units % 100:02d}"
    query = urlencode({"amount": amount})
    url = f"https://{base.netloc}{base.path}?{query}"
    # No authorization headers, cookies, API client, or cached success.
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status != 200 or response.geturl() != url:
            raise StarlingValidationError("Settle Up page redirected or did not return HTTP 200; supply a fresh app link")
        page = RequestPage()
        page.feed(response.read(1_000_000).decode("utf-8"))
    if page.recipient.strip() != expected or f"{base.path}/pay?{query}" not in page.links:
        raise StarlingValidationError("Settle Up recipient or amount link could not be verified; supply a fresh app link")
    return url, expected, amount
