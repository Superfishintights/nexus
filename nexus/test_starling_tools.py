from __future__ import annotations

import ssl

from nexus.test_helpers import add_tool_pack_paths

add_tool_pack_paths(("nexus_tools_starling",))

from nexus_tools_starling import curated  # noqa: E402
from nexus_tools_starling import client as starling_client_module  # noqa: E402
from nexus_tools_starling.client import StarlingClient  # noqa: E402
from nexus_tools_starling.manifest import (  # noqa: E402
    TOKEN_PROFILE_PAYMENT_INITIATION,
    TOKEN_PROFILE_PAYEE_SAVINGS_CREATE,
    TOKEN_PROFILE_READ_EDIT,
    requires_signature,
    resolve_token_profile,
)


class FakeClient:
    def __init__(self, responses: dict[tuple[str, str], object]):
        self.responses = responses

    def get(self, endpoint: str, params=None, **kwargs):  # noqa: ANN001
        key = ("GET", endpoint)
        if key not in self.responses:
            raise AssertionError(f"Unexpected GET {endpoint}")
        return self.responses[key]

    def put(self, endpoint: str, body=None, params=None, **kwargs):  # noqa: ANN001
        key = ("PUT", endpoint)
        if key not in self.responses:
            raise AssertionError(f"Unexpected PUT {endpoint}")
        return self.responses[key]

    def delete(self, endpoint: str, params=None, **kwargs):  # noqa: ANN001
        key = ("DELETE", endpoint)
        if key not in self.responses:
            raise AssertionError(f"Unexpected DELETE {endpoint}")
        return self.responses[key]


class FakeHeaders:
    def get_content_type(self) -> str:
        return "application/json"

    def get_content_charset(self) -> str:
        return "utf-8"

    def get(self, name: str, default=None):  # noqa: ANN001
        return default


class FakeHTTPResponse:
    headers = FakeHeaders()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        return False

    def read(self) -> bytes:
        return b"{}"


def _capture_authorization_header(monkeypatch, client: StarlingClient, method: str, endpoint: str) -> str:
    captured: dict[str, str] = {}

    def fake_urlopen(request, timeout=None, context=None):  # noqa: ANN001
        captured["authorization"] = request.get_header("Authorization") or ""
        return FakeHTTPResponse()

    monkeypatch.setattr(starling_client_module.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(client, "_build_signing_headers", lambda **kwargs: {})

    if method == "GET":
        client.get(endpoint)
    elif method == "PUT":
        client.put(endpoint, body={})
    elif method == "DELETE":
        client.delete(endpoint)
    else:  # pragma: no cover
        raise AssertionError(f"Unsupported test method: {method}")

    return captured["authorization"]


def test_requires_signature_matches_signed_public_endpoints() -> None:
    assert requires_signature("PUT", "account-holder/individual/email")
    assert requires_signature("POST", "addresses")
    assert requires_signature("PUT", "payments/local/account/a/category/b")
    assert requires_signature("DELETE", "payments/local/account/a/category/b/standing-orders/c")
    assert not requires_signature("GET", "accounts/a/balance")


def test_resolve_token_profile_matches_special_cases() -> None:
    assert resolve_token_profile("GET", "accounts/acct-1/balance") == TOKEN_PROFILE_READ_EDIT
    assert resolve_token_profile("PUT", "payees") == TOKEN_PROFILE_PAYEE_SAVINGS_CREATE
    assert resolve_token_profile("PUT", "feed/account/acct-1/round-up") == TOKEN_PROFILE_PAYEE_SAVINGS_CREATE
    assert (
        resolve_token_profile("PUT", "account/acct-1/savings-goals/goal-1")
        == TOKEN_PROFILE_PAYEE_SAVINGS_CREATE
    )
    assert (
        resolve_token_profile("PUT", "account/acct-1/savings-goals/goal-1/add-money/transfer-1")
        == TOKEN_PROFILE_PAYEE_SAVINGS_CREATE
    )
    assert (
        resolve_token_profile("PUT", "payments/local/account/acct-1/category/cat-1")
        == TOKEN_PROFILE_PAYMENT_INITIATION
    )
    assert (
        resolve_token_profile("DELETE", "feed/account/acct-1/round-up")
        == TOKEN_PROFILE_READ_EDIT
    )
    assert (
        resolve_token_profile("DELETE", "payments/local/account/acct-1/category/cat-1/standing-orders/order-1")
        == TOKEN_PROFILE_PAYMENT_INITIATION
    )


def test_starling_client_routes_requests_to_the_matching_token(monkeypatch) -> None:
    monkeypatch.setenv("STARLING_TOKEN_READ_EDIT", "read-token")
    monkeypatch.setenv("STARLING_TOKEN_PAYEE_SAVINGS_CREATE", "payee-savings-token")
    monkeypatch.setenv("STARLING_TOKEN_PAYMENT_INITIATION", "payment-token")

    client = StarlingClient(base_url="https://api.starlingbank.com", ssl_context=ssl.create_default_context())

    assert _capture_authorization_header(monkeypatch, client, "GET", "accounts/acct-1/balance") == "Bearer read-token"
    assert _capture_authorization_header(monkeypatch, client, "PUT", "payees") == "Bearer payee-savings-token"
    assert (
        _capture_authorization_header(monkeypatch, client, "PUT", "account/acct-1/savings-goals/goal-1")
        == "Bearer payee-savings-token"
    )
    assert (
        _capture_authorization_header(
            monkeypatch,
            client,
            "PUT",
            "payments/local/account/acct-1/category/cat-1/standing-orders",
        )
        == "Bearer payment-token"
    )


def test_starling_client_falls_back_to_read_edit_token_when_specialized_tokens_are_unset(monkeypatch) -> None:
    monkeypatch.setenv("STARLING_TOKEN_READ_EDIT", "read-token")
    monkeypatch.delenv("STARLING_TOKEN_PAYEE_SAVINGS_CREATE", raising=False)
    monkeypatch.delenv("STARLING_TOKEN_PAYMENT_INITIATION", raising=False)

    client = StarlingClient(base_url="https://api.starlingbank.com", ssl_context=ssl.create_default_context())

    assert _capture_authorization_header(monkeypatch, client, "PUT", "payees") == "Bearer read-token"
    assert (
        _capture_authorization_header(
            monkeypatch,
            client,
            "DELETE",
            "payments/local/account/acct-1/category/cat-1/standing-orders/order-1",
        )
        == "Bearer read-token"
    )
    assert _capture_authorization_header(monkeypatch, client, "PUT", "feed/account/acct-1/round-up") == "Bearer read-token"


def test_normalize_feed_item_tracks_signed_direction() -> None:
    normalized = curated._normalize_feed_item(
        {
            "feedItemUid": "feed-1",
            "amount": {"currency": "GBP", "minorUnits": 1234},
            "direction": "OUT",
            "status": "SETTLED",
            "transactionTime": "2026-03-01T10:00:00.000Z",
            "counterPartyName": "Coffee Shop",
            "reference": "LATTE",
            "source": "MASTER_CARD",
        }
    )

    assert normalized["currency"] == "GBP"
    assert normalized["outflow_minor_units"] == 1234
    assert normalized["signed_minor_units"] == -1234
    assert normalized["merchant_key"]


def test_recurring_outflows_detect_monthly_pattern() -> None:
    items = [
        {
            "merchant_key": "merchant-1",
            "counterparty_name": "Music Service",
            "reference": "SUB",
            "source": "DIRECT_DEBIT",
            "currency": "GBP",
            "direction": "OUT",
            "status": "SETTLED",
            "outflow_minor_units": 999,
            "event_date": "2026-01-05",
        },
        {
            "merchant_key": "merchant-1",
            "counterparty_name": "Music Service",
            "reference": "SUB",
            "source": "DIRECT_DEBIT",
            "currency": "GBP",
            "direction": "OUT",
            "status": "SETTLED",
            "outflow_minor_units": 999,
            "event_date": "2026-02-05",
        },
        {
            "merchant_key": "merchant-1",
            "counterparty_name": "Music Service",
            "reference": "SUB",
            "source": "DIRECT_DEBIT",
            "currency": "GBP",
            "direction": "OUT",
            "status": "SETTLED",
            "outflow_minor_units": 999,
            "event_date": "2026-03-05",
        },
    ]

    recurring = curated._recurring_outflows(items, min_occurrences=2)

    assert len(recurring) == 1
    assert recurring[0]["cadence"] == "monthly"
    assert recurring[0]["typical_outflow_minor_units"] == 999


def test_get_account_snapshot_builds_expected_envelope(monkeypatch) -> None:
    fake_client = FakeClient(
        {
            (
                "GET",
                "accounts",
            ): {
                "accounts": [
                    {
                        "accountUid": "acct-1",
                        "defaultCategory": "cat-1",
                        "name": "Personal",
                        "accountType": "PRIMARY",
                        "currency": "GBP",
                    }
                ]
            },
            (
                "GET",
                "accounts/acct-1/balance",
            ): {
                "effectiveBalance": {"currency": "GBP", "minorUnits": 125000}
            },
            ("GET", "accounts/acct-1/identifiers"): {"accountIdentifier": "12345678"},
            ("GET", "account-holder"): {"accountHolderUid": "holder-1"},
        }
    )
    monkeypatch.setattr(curated, "get_client", lambda: fake_client)

    result = curated.get_account_snapshot()

    assert result["ok"] is True
    assert result["operation"] == "starling.get_account_snapshot"
    assert result["summary"]["effective_balance"]["minor_units"] == 125000
    assert result["data"]["account"]["name"] == "Personal"
