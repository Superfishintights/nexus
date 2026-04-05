from __future__ import annotations

from nexus.test_helpers import add_tool_pack_paths

add_tool_pack_paths(("nexus_tools_starling",))

from nexus_tools_starling import curated
from nexus_tools_starling.manifest import requires_signature


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


def test_requires_signature_matches_signed_public_endpoints() -> None:
    assert requires_signature("PUT", "account-holder/individual/email")
    assert requires_signature("POST", "addresses")
    assert requires_signature("PUT", "payments/local/account/a/category/b")
    assert requires_signature("DELETE", "payments/local/account/a/category/b/standing-orders/c")
    assert not requires_signature("GET", "accounts/a/balance")


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
