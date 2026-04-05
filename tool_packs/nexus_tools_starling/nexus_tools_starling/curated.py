"""Curated Starling finance and automation tools."""

from __future__ import annotations

import calendar
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from statistics import median
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from nexus.config import get_setting
from nexus.tool_registry import register_tool

from .client import get_client
from .errors import StarlingValidationError

SCHEMA_VERSION = "1.0"
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_MAX_PAGES = 10
TOP_ITEMS = 10

CARD_CONTROL_ENDPOINTS = {
    "enabled": "controls/enabled",
    "atm_enabled": "controls/atm-enabled",
    "currency_switch_enabled": "controls/currency-switch",
    "gambling_enabled": "controls/gambling-enabled",
    "mag_stripe_enabled": "controls/mag-stripe-enabled",
    "mobile_wallet_enabled": "controls/mobile-wallet-enabled",
    "online_enabled": "controls/online-enabled",
    "pos_enabled": "controls/pos-enabled",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str, *, end_of_day: bool = False) -> datetime:
    text = value.strip()
    if "T" in text:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    parsed_date = date.fromisoformat(text)
    parsed_time = time.max if end_of_day else time.min
    return datetime.combine(parsed_date, parsed_time, tzinfo=timezone.utc)


def _coerce_range(
    start_date: Optional[str],
    end_date: Optional[str],
    *,
    default_days: int = DEFAULT_LOOKBACK_DAYS,
) -> tuple[datetime, datetime]:
    end_value = _parse_datetime(end_date, end_of_day=True) if end_date else _utc_now()
    start_value = (
        _parse_datetime(start_date)
        if start_date
        else end_value - timedelta(days=max(default_days, 1))
    )
    if start_value > end_value:
        raise StarlingValidationError("start_date must be before end_date")
    return start_value, end_value


def _month_bounds(month_label: str) -> tuple[datetime, datetime]:
    year_text, month_text = month_label.split("-", 1)
    year = int(year_text)
    month = int(month_text)
    _, last_day = calendar.monthrange(year, month)
    start_value = datetime(year, month, 1, tzinfo=timezone.utc)
    end_value = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    return start_value, end_value


def _minor_units(amount: Optional[Dict[str, Any]]) -> int:
    if not isinstance(amount, dict):
        return 0
    value = amount.get("minorUnits")
    return int(value) if value is not None else 0


def _currency(amount: Optional[Dict[str, Any]], fallback: str = "GBP") -> str:
    if not isinstance(amount, dict):
        return fallback
    value = amount.get("currency")
    return str(value) if value else fallback


def _money(currency: str, minor_units: int) -> Dict[str, Any]:
    return {"currency": currency, "minor_units": int(minor_units)}


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _round2(value: float) -> float:
    return round(float(value), 2)


def _envelope(
    operation: str,
    *,
    inputs: Dict[str, Any],
    summary: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    derived: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    next_cursor: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    ok: bool = True,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "source": "starling",
        "operation": operation,
        "inputs": inputs,
        "summary": summary or {},
        "data": data or {},
        "derived": derived or {},
        "warnings": warnings or [],
        "next_cursor": next_cursor,
        "actions": actions or [],
    }


def _load_accounts(client: Any) -> List[Dict[str, Any]]:
    payload = client.get("accounts") or {}
    accounts = payload.get("accounts") or []
    return [account for account in accounts if isinstance(account, dict)]


def _resolve_account_context(
    client: Any,
    *,
    account_uid: Optional[str],
    category_uid: Optional[str],
) -> Dict[str, Any]:
    accounts = _load_accounts(client)
    if not accounts and not account_uid:
        raise StarlingValidationError("No Starling accounts were returned and no account_uid was provided")

    configured_account_uid = get_setting("STARLING_ACCOUNT_UID")
    selected_account: Optional[Dict[str, Any]] = None
    desired_account_uid = account_uid or configured_account_uid
    if desired_account_uid:
        selected_account = next(
            (account for account in accounts if account.get("accountUid") == desired_account_uid),
            None,
        )
        if selected_account is None and accounts:
            raise StarlingValidationError(f"Unknown account_uid: {desired_account_uid}")
    elif accounts:
        selected_account = accounts[0]

    resolved_account_uid = (
        desired_account_uid
        if desired_account_uid and not selected_account
        else (selected_account or {}).get("accountUid")
    )
    if not resolved_account_uid:
        raise StarlingValidationError("Unable to resolve a Starling account UID")

    resolved_category_uid = category_uid or (selected_account or {}).get("defaultCategory")
    return {
        "account_uid": resolved_account_uid,
        "category_uid": resolved_category_uid,
        "selected_account": selected_account,
        "accounts": accounts,
    }


def _extract_next_page(links: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    next_link = links.get("next")
    if not isinstance(next_link, str) or not next_link:
        return None, None
    parsed = urlparse(next_link)
    query = parse_qs(parsed.query)
    cursor = (query.get("cursor") or [None])[0]
    page_to_fetch = (query.get("pageToFetch") or [None])[0]
    return cursor, page_to_fetch


def _normalize_feed_item(item: Dict[str, Any]) -> Dict[str, Any]:
    amount = item.get("amount") if isinstance(item.get("amount"), dict) else {}
    minor_units = _minor_units(amount)
    currency = _currency(amount)
    direction = str(item.get("direction") or "")
    status = str(item.get("status") or "")
    transaction_time = item.get("transactionTime")
    settlement_time = item.get("settlementTime")
    updated_at = item.get("updatedAt")
    event_time = settlement_time or transaction_time or updated_at
    event_date = event_time[:10] if isinstance(event_time, str) and len(event_time) >= 10 else None
    counterparty_name = item.get("counterPartyName") or item.get("counterPartySubEntityName")
    reference = item.get("reference")
    source = item.get("source")
    merchant_key = (
        item.get("counterPartyUid")
        or item.get("counterPartySubEntityUid")
        or "|".join(str(value or "") for value in (counterparty_name, reference, source))
    )
    signed_minor_units = minor_units if direction == "IN" else -minor_units

    return {
        "feed_item_uid": item.get("feedItemUid"),
        "category_uid": item.get("categoryUid"),
        "direction": direction,
        "status": status,
        "currency": currency,
        "minor_units": minor_units,
        "signed_minor_units": signed_minor_units,
        "inflow_minor_units": minor_units if direction == "IN" else 0,
        "outflow_minor_units": minor_units if direction == "OUT" else 0,
        "transaction_time": transaction_time,
        "settlement_time": settlement_time,
        "updated_at": updated_at,
        "event_time": event_time,
        "event_date": event_date,
        "counterparty_name": counterparty_name,
        "counterparty_uid": item.get("counterPartyUid"),
        "counterparty_account_uid": item.get("counterPartySubEntityUid"),
        "reference": reference,
        "source": source,
        "source_sub_type": item.get("sourceSubType"),
        "spending_category": item.get("spendingCategory") or "UNCATEGORIZED",
        "raw": item,
        "merchant_key": merchant_key,
    }


def _fetch_feed_items(
    client: Any,
    *,
    account_uid: str,
    category_uid: Optional[str],
    start_value: datetime,
    end_value: datetime,
    settled_only: bool,
    include_pending: bool,
    max_pages: int,
) -> List[Dict[str, Any]]:
    params = {
        "minTransactionTimestamp": _isoformat(start_value),
        "maxTransactionTimestamp": _isoformat(end_value),
    }
    raw_items: List[Dict[str, Any]] = []
    if settled_only:
        payload = client.get(
            f"feed/account/{account_uid}/settled-transactions-between",
            params=params,
        ) or {}
        raw_items = [
            item for item in (payload.get("feedItems") or []) if isinstance(item, dict)
        ]
    else:
        if not category_uid:
            raise StarlingValidationError("category_uid is required for non-settled feed queries")

        cursor: Optional[str] = None
        page_to_fetch: Optional[str] = None
        seen_ids: set[str] = set()
        for _ in range(max(max_pages, 1)):
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            if page_to_fetch:
                page_params["pageToFetch"] = page_to_fetch

            payload = client.get(
                f"feed/account/{account_uid}/category/{category_uid}/paginated-transactions",
                params=page_params,
            ) or {}
            for item in payload.get("feedItems") or []:
                if not isinstance(item, dict):
                    continue
                feed_item_uid = str(item.get("feedItemUid") or "")
                if feed_item_uid and feed_item_uid in seen_ids:
                    continue
                if feed_item_uid:
                    seen_ids.add(feed_item_uid)
                raw_items.append(item)

            cursor, page_to_fetch = _extract_next_page(payload.get("links") or {})
            if not cursor:
                break

    normalized = [_normalize_feed_item(item) for item in raw_items]
    if not include_pending:
        blocked_statuses = {"PENDING", "UPCOMING", "UPCOMING_CANCELLED", "RETRYING", "ACCOUNT_CHECK"}
        normalized = [item for item in normalized if item["status"] not in blocked_statuses]
    normalized.sort(key=lambda item: item.get("event_time") or "")
    return normalized


def _summarize_flow(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items_list = list(items)
    inflow_minor_units = sum(item["inflow_minor_units"] for item in items_list)
    outflow_minor_units = sum(item["outflow_minor_units"] for item in items_list)
    net_minor_units = inflow_minor_units - outflow_minor_units
    currency = items_list[0]["currency"] if items_list else "GBP"
    return {
        "count": len(items_list),
        "inflow": _money(currency, inflow_minor_units),
        "outflow": _money(currency, outflow_minor_units),
        "net": _money(currency, net_minor_units),
    }


def _top_counterparties(items: Iterable[Dict[str, Any]], *, limit: int = TOP_ITEMS) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if item["direction"] != "OUT":
            continue
        key = item["merchant_key"]
        bucket = grouped.setdefault(
            key,
            {
                "merchant_key": key,
                "name": item["counterparty_name"] or item["reference"] or item["source"] or "Unknown",
                "currency": item["currency"],
                "outflow_minor_units": 0,
                "count": 0,
            },
        )
        bucket["outflow_minor_units"] += item["outflow_minor_units"]
        bucket["count"] += 1

    ranked = sorted(
        grouped.values(),
        key=lambda value: (-value["outflow_minor_units"], -value["count"], value["name"]),
    )
    return ranked[:limit]


def _bucket_key(event_date: str, bucket: str) -> str:
    year = int(event_date[0:4])
    month = int(event_date[5:7])
    day = int(event_date[8:10])
    if bucket == "month":
        return f"{year:04d}-{month:02d}"
    if bucket == "week":
        iso_year, iso_week, _ = date(year, month, day).isocalendar()
        return f"{iso_year:04d}-W{iso_week:02d}"
    return f"{year:04d}-{month:02d}-{day:02d}"


def _timeseries(items: Iterable[Dict[str, Any]], *, bucket: str) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if not item.get("event_date"):
            continue
        key = _bucket_key(item["event_date"], bucket)
        bucket_row = grouped.setdefault(
            key,
            {
                "bucket": key,
                "currency": item["currency"],
                "inflow_minor_units": 0,
                "outflow_minor_units": 0,
                "net_minor_units": 0,
                "count": 0,
            },
        )
        bucket_row["inflow_minor_units"] += item["inflow_minor_units"]
        bucket_row["outflow_minor_units"] += item["outflow_minor_units"]
        bucket_row["net_minor_units"] += item["signed_minor_units"]
        bucket_row["count"] += 1

    return [grouped[key] for key in sorted(grouped)]


def _recurring_outflows(
    items: Iterable[Dict[str, Any]],
    *,
    min_occurrences: int = 2,
) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        if item["direction"] != "OUT" or item["status"] != "SETTLED" or not item.get("event_date"):
            continue
        grouped[item["merchant_key"]].append(item)

    candidates: List[Dict[str, Any]] = []
    for merchant_key, group in grouped.items():
        if len(group) < min_occurrences:
            continue
        ordered = sorted(group, key=lambda item: item["event_date"] or "")
        dates = [date.fromisoformat(item["event_date"]) for item in ordered if item.get("event_date")]
        if len(dates) < min_occurrences:
            continue
        gaps = [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]
        if not gaps:
            continue

        median_gap = int(round(float(median(gaps))))
        if median_gap < 5 or median_gap > 45:
            continue

        amounts = [item["outflow_minor_units"] for item in ordered]
        median_amount = int(round(float(median(amounts))))
        if median_amount <= 0:
            continue

        max_deviation_ratio = max(abs(amount - median_amount) for amount in amounts) / max(median_amount, 1)
        if max_deviation_ratio > 0.75:
            continue

        cadence = "irregular"
        if 6 <= median_gap <= 8:
            cadence = "weekly"
        elif 12 <= median_gap <= 16:
            cadence = "biweekly"
        elif 25 <= median_gap <= 35:
            cadence = "monthly"

        next_expected_date = dates[-1] + timedelta(days=median_gap)
        exemplar = ordered[-1]
        candidates.append(
            {
                "merchant_key": merchant_key,
                "name": exemplar["counterparty_name"] or exemplar["reference"] or exemplar["source"] or "Unknown",
                "currency": exemplar["currency"],
                "occurrences": len(ordered),
                "typical_outflow_minor_units": median_amount,
                "median_gap_days": median_gap,
                "cadence": cadence,
                "last_seen_date": dates[-1].isoformat(),
                "next_expected_date": next_expected_date.isoformat(),
            }
        )

    candidates.sort(key=lambda item: (-item["typical_outflow_minor_units"], item["name"]))
    return candidates


def _month_stats(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items_list = list(items)
    summary = _summarize_flow(items_list)
    by_category: Dict[str, int] = defaultdict(int)
    for item in items_list:
        if item["direction"] == "OUT":
            by_category[item["spending_category"]] += item["outflow_minor_units"]
    top_categories = sorted(by_category.items(), key=lambda pair: (-pair[1], pair[0]))[:TOP_ITEMS]
    return {
        "count": summary["count"],
        "currency": summary["outflow"]["currency"],
        "inflow_minor_units": summary["inflow"]["minor_units"],
        "outflow_minor_units": summary["outflow"]["minor_units"],
        "net_minor_units": summary["net"]["minor_units"],
        "top_categories": [
            {"spending_category": name, "outflow_minor_units": amount} for name, amount in top_categories
        ],
    }


def _prepare_payment_body(body: Dict[str, Any], *, ensure_external_identifier: bool) -> Dict[str, Any]:
    prepared = dict(body)
    if ensure_external_identifier and not prepared.get("externalIdentifier"):
        prepared["externalIdentifier"] = str(uuid4())
    return prepared


def _forecast_next_30_days_data(
    client: Any,
    *,
    account_uid: str,
    category_uid: Optional[str],
) -> Dict[str, Any]:
    now = _utc_now()
    history_start = now - timedelta(days=120)
    history = _fetch_feed_items(
        client,
        account_uid=account_uid,
        category_uid=category_uid,
        start_value=history_start,
        end_value=now,
        settled_only=True,
        include_pending=False,
        max_pages=DEFAULT_MAX_PAGES,
    )
    recurring = _recurring_outflows(history, min_occurrences=2)
    recurring_by_key = {candidate["merchant_key"] for candidate in recurring}
    window_end = (now + timedelta(days=30)).date()
    recurring_due = [
        candidate
        for candidate in recurring
        if now.date() < date.fromisoformat(candidate["next_expected_date"]) <= window_end
    ]
    recurring_outflow_minor_units = sum(
        candidate["typical_outflow_minor_units"] for candidate in recurring_due
    )

    recent_start = now - timedelta(days=30)
    discretionary_recent = [
        item
        for item in history
        if item["direction"] == "OUT"
        and item["merchant_key"] not in recurring_by_key
        and item.get("event_time")
        and _parse_datetime(item["event_time"]) >= recent_start
    ]
    recent_inflows = [
        item
        for item in history
        if item["direction"] == "IN"
        and item.get("event_time")
        and _parse_datetime(item["event_time"]) >= recent_start
    ]
    currency = history[0]["currency"] if history else "GBP"
    discretionary_outflow_minor_units = sum(
        item["outflow_minor_units"] for item in discretionary_recent
    )
    projected_discretionary_outflow_minor_units = int(
        round(discretionary_outflow_minor_units * _safe_ratio(30, 30))
    )
    projected_inflow_minor_units = sum(item["inflow_minor_units"] for item in recent_inflows)
    projected_total_outflow_minor_units = (
        recurring_outflow_minor_units + projected_discretionary_outflow_minor_units
    )

    return {
        "currency": currency,
        "projected_inflow_minor_units": projected_inflow_minor_units,
        "projected_outflow_minor_units": projected_total_outflow_minor_units,
        "projected_net_minor_units": projected_inflow_minor_units - projected_total_outflow_minor_units,
        "recurring_due": recurring_due,
        "recurring_outflow_minor_units": recurring_outflow_minor_units,
        "projected_discretionary_outflow_minor_units": projected_discretionary_outflow_minor_units,
    }


def _find_card(cards: Iterable[Dict[str, Any]], card_uid: str) -> Optional[Dict[str, Any]]:
    return next((card for card in cards if card.get("cardUid") == card_uid), None)


def _collect_card_control_changes(
    *,
    enabled: Optional[bool],
    atm_enabled: Optional[bool],
    currency_switch_enabled: Optional[bool],
    gambling_enabled: Optional[bool],
    mag_stripe_enabled: Optional[bool],
    mobile_wallet_enabled: Optional[bool],
    online_enabled: Optional[bool],
    pos_enabled: Optional[bool],
) -> Dict[str, bool]:
    values = {
        "enabled": enabled,
        "atm_enabled": atm_enabled,
        "currency_switch_enabled": currency_switch_enabled,
        "gambling_enabled": gambling_enabled,
        "mag_stripe_enabled": mag_stripe_enabled,
        "mobile_wallet_enabled": mobile_wallet_enabled,
        "online_enabled": online_enabled,
        "pos_enabled": pos_enabled,
    }
    return {key: value for key, value in values.items() if value is not None}


@register_tool(
    namespace="starling",
    description="Get an account balance using the configured or supplied Starling account UID.",
    examples=[
        'load_tool("starling.get_account_balance")()',
    ],
    aliases=[],
)
def get_account_balance(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    return client.get(f"accounts/{context['account_uid']}/balance")


@register_tool(
    namespace="starling",
    description="Get all spaces for the configured or supplied Starling account UID.",
    examples=[
        'load_tool("starling.get_spaces")()',
    ],
    aliases=[],
)
def get_spaces(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    return client.get(f"account/{context['account_uid']}/spaces")


@register_tool(
    namespace="starling",
    description="Get all savings goals for the configured or supplied Starling account UID.",
    examples=[
        'load_tool("starling.get_savings_goals")()',
    ],
    aliases=[],
)
def get_savings_goals(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    return client.get(f"account/{context['account_uid']}/savings-goals")


@register_tool(
    namespace="starling",
    description="List standing orders for the configured or supplied Starling account and category.",
    examples=[
        'load_tool("starling.get_standing_orders")()',
    ],
    aliases=[],
)
def get_standing_orders(
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    if not context["category_uid"]:
        raise StarlingValidationError("category_uid is required to list standing orders")
    return client.get(
        f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}/standing-orders"
    )


@register_tool(
    namespace="starling",
    description="Query feed items between two timestamps for the configured or supplied account and category.",
    examples=[
        'load_tool("starling.query_feed_items_by_category_between")(start_date="2026-03-01", end_date="2026-03-31")',
    ],
    aliases=[],
)
def query_feed_items_by_category_between(
    start_date: str,
    end_date: str,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    settled_only: bool = False,
    include_pending: bool = False,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=settled_only,
        include_pending=include_pending,
        max_pages=max_pages,
    )
    return {
        "account_uid": context["account_uid"],
        "category_uid": context["category_uid"],
        "count": len(items),
        "feed_items": items,
    }


@register_tool(
    namespace="starling",
    description="Get a one-call snapshot of the selected Starling account, including balance and identifiers.",
    examples=[
        'load_tool("starling.get_account_snapshot")()',
    ],
    aliases=[],
)
def get_account_snapshot(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    selected_account = context["selected_account"] or {}
    balance = client.get(f"accounts/{context['account_uid']}/balance") or {}
    identifiers = client.get(f"accounts/{context['account_uid']}/identifiers") or {}
    account_holder = client.get("account-holder") or {}
    return _envelope(
        "starling.get_account_snapshot",
        inputs={"account_uid": context["account_uid"]},
        summary={
            "account_name": selected_account.get("name"),
            "account_type": selected_account.get("accountType"),
            "currency": selected_account.get("currency"),
            "effective_balance": {
                "currency": _currency(balance.get("effectiveBalance")),
                "minor_units": _minor_units(balance.get("effectiveBalance")),
            },
            "accounts_count": len(context["accounts"]),
        },
        data={
            "account_holder": account_holder,
            "account": selected_account,
            "balance": balance,
            "identifiers": identifiers,
        },
    )


@register_tool(
    namespace="starling",
    description="Summarize Starling spaces and balances across savings goals and spending spaces.",
    examples=[
        'load_tool("starling.get_spaces_overview")()',
    ],
    aliases=[],
)
def get_spaces_overview(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    spaces = client.get(f"account/{context['account_uid']}/spaces") or {}
    spending_spaces = [space for space in spaces.get("spendingSpaces") or [] if isinstance(space, dict)]
    savings_spaces = [goal for goal in spaces.get("savingsGoals") or [] if isinstance(goal, dict)]
    spending_total = sum(_minor_units(space.get("balance")) for space in spending_spaces)
    savings_total = sum(_minor_units(goal.get("totalSaved")) for goal in savings_spaces)
    currency = (
        _currency(spending_spaces[0].get("balance")) if spending_spaces else _currency(savings_spaces[0].get("totalSaved"))
    )
    return _envelope(
        "starling.get_spaces_overview",
        inputs={"account_uid": context["account_uid"]},
        summary={
            "spending_space_count": len(spending_spaces),
            "savings_goal_count": len(savings_spaces),
            "spending_space_total": _money(currency, spending_total),
            "savings_goal_total": _money(currency, savings_total),
        },
        data={
            "spending_spaces": spending_spaces,
            "savings_goals": savings_spaces,
        },
    )


@register_tool(
    namespace="starling",
    description="Summarize Starling savings goals, targets, and progress for the selected account.",
    examples=[
        'load_tool("starling.get_savings_goals_overview")()',
    ],
    aliases=[],
)
def get_savings_goals_overview(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    payload = client.get(f"account/{context['account_uid']}/savings-goals") or {}
    goals = [goal for goal in payload.get("savingsGoalList") or [] if isinstance(goal, dict)]
    total_saved = sum(_minor_units(goal.get("totalSaved")) for goal in goals)
    total_target = sum(_minor_units(goal.get("target")) for goal in goals)
    currency = _currency(goals[0].get("totalSaved")) if goals else "GBP"
    return _envelope(
        "starling.get_savings_goals_overview",
        inputs={"account_uid": context["account_uid"]},
        summary={
            "goal_count": len(goals),
            "total_saved": _money(currency, total_saved),
            "total_target": _money(currency, total_target),
            "funded_ratio": _round2(_safe_ratio(total_saved, total_target)),
        },
        data={"savings_goals": goals},
    )


@register_tool(
    namespace="starling",
    description="Summarize card lock state and controls across Starling cards.",
    examples=[
        'load_tool("starling.get_cards_overview")()',
    ],
    aliases=[],
)
def get_cards_overview() -> Dict[str, Any]:
    client = get_client()
    payload = client.get("cards") or {}
    cards = [card for card in payload.get("cards") or [] if isinstance(card, dict)]
    return _envelope(
        "starling.get_cards_overview",
        inputs={},
        summary={
            "card_count": len(cards),
            "enabled_count": sum(1 for card in cards if card.get("enabled")),
            "locked_count": sum(1 for card in cards if not card.get("enabled")),
            "cancelled_count": sum(1 for card in cards if card.get("cancelled")),
        },
        data={"cards": cards},
    )


@register_tool(
    namespace="starling",
    description="Summarize saved payees and optionally scheduled payments for Starling payee accounts.",
    examples=[
        'load_tool("starling.get_payees_overview")()',
    ],
    aliases=[],
)
def get_payees_overview(include_scheduled_payments: bool = False) -> Dict[str, Any]:
    client = get_client()
    payload = client.get("payees") or {}
    payees = [payee for payee in payload.get("payees") or [] if isinstance(payee, dict)]
    account_count = sum(len(payee.get("accounts") or []) for payee in payees)
    scheduled_payments: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if include_scheduled_payments:
        for payee in payees:
            for account in payee.get("accounts") or []:
                account_uid = account.get("payeeAccountUid")
                payee_uid = payee.get("payeeUid")
                if not account_uid or not payee_uid:
                    continue
                response = client.get(
                    f"payees/{payee_uid}/account/{account_uid}/scheduled-payments"
                ) or {}
                for payment in response.get("scheduledPayments") or []:
                    if isinstance(payment, dict):
                        scheduled_payments.append(payment)
    else:
        warnings.append("Scheduled payment lookups were skipped; set include_scheduled_payments=true to fetch them.")

    return _envelope(
        "starling.get_payees_overview",
        inputs={"include_scheduled_payments": include_scheduled_payments},
        summary={
            "payee_count": len(payees),
            "payee_account_count": account_count,
            "scheduled_payment_count": len(scheduled_payments),
        },
        data={
            "payees": payees,
            "scheduled_payments": scheduled_payments,
        },
        warnings=warnings,
    )


@register_tool(
    namespace="starling",
    description="Summarize direct debit mandates, statuses, and upcoming dates for the selected Starling account.",
    examples=[
        'load_tool("starling.get_direct_debit_overview")()',
    ],
    aliases=[],
)
def get_direct_debit_overview(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    if account_uid:
        payload = client.get(f"direct-debit/mandates/account/{account_uid}") or {}
    else:
        payload = client.get("direct-debit/mandates") or {}
    mandates = [mandate for mandate in payload.get("mandates") or [] if isinstance(mandate, dict)]
    statuses = Counter(str(mandate.get("status") or "UNKNOWN") for mandate in mandates)
    upcoming = sorted(
        [
            {
                "uid": mandate.get("uid"),
                "reference": mandate.get("reference"),
                "originator_name": mandate.get("originatorName"),
                "next_date": mandate.get("nextDate"),
                "last_payment": mandate.get("lastPayment"),
            }
            for mandate in mandates
            if mandate.get("nextDate")
        ],
        key=lambda item: str(item["next_date"]),
    )[:TOP_ITEMS]
    return _envelope(
        "starling.get_direct_debit_overview",
        inputs={"account_uid": account_uid},
        summary={
            "mandate_count": len(mandates),
            "status_counts": dict(statuses),
            "upcoming_count": len(upcoming),
        },
        data={"mandates": mandates, "upcoming": upcoming},
    )


@register_tool(
    namespace="starling",
    description="Combine account balance with spaces and savings goal balances to show current cash position.",
    examples=[
        'load_tool("starling.get_cash_position")()',
    ],
    aliases=[],
)
def get_cash_position(account_uid: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    balance = client.get(f"accounts/{context['account_uid']}/balance") or {}
    spaces = client.get(f"account/{context['account_uid']}/spaces") or {}
    spending_spaces = [space for space in spaces.get("spendingSpaces") or [] if isinstance(space, dict)]
    savings_goals = [goal for goal in spaces.get("savingsGoals") or [] if isinstance(goal, dict)]
    effective_balance = _minor_units(balance.get("effectiveBalance"))
    spending_space_total = sum(_minor_units(space.get("balance")) for space in spending_spaces)
    savings_goal_total = sum(_minor_units(goal.get("totalSaved")) for goal in savings_goals)
    currency = _currency(balance.get("effectiveBalance"))
    return _envelope(
        "starling.get_cash_position",
        inputs={"account_uid": context["account_uid"]},
        summary={
            "effective_balance": _money(currency, effective_balance),
            "spending_space_total": _money(currency, spending_space_total),
            "savings_goal_total": _money(currency, savings_goal_total),
            "tracked_total": _money(
                currency,
                effective_balance + spending_space_total + savings_goal_total,
            ),
        },
        data={
            "balance": balance,
            "spending_spaces": spending_spaces,
            "savings_goals": savings_goals,
        },
    )


@register_tool(
    namespace="starling",
    description="Build an inflow and outflow time series from Starling feed items over a date range.",
    examples=[
        'load_tool("starling.get_spending_timeseries")(start_date="2026-03-01", end_date="2026-03-31")',
    ],
    aliases=[],
)
def get_spending_timeseries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    bucket: str = "day",
    settled_only: bool = True,
    include_pending: bool = False,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    if bucket not in {"day", "week", "month"}:
        raise StarlingValidationError("bucket must be one of: day, week, month")
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=settled_only,
        include_pending=include_pending,
        max_pages=max_pages,
    )
    series = _timeseries(items, bucket=bucket)
    return _envelope(
        "starling.get_spending_timeseries",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "start_date": _isoformat(start_value),
            "end_date": _isoformat(end_value),
            "bucket": bucket,
            "settled_only": settled_only,
            "include_pending": include_pending,
        },
        summary={
            "series_length": len(series),
            "transaction_count": len(items),
            "bucket": bucket,
        },
        data={"series": series},
        derived={"cashflow": _summarize_flow(items)},
    )


@register_tool(
    namespace="starling",
    description="Summarize Starling transactions over a date range with cashflow totals and top counterparties.",
    examples=[
        'load_tool("starling.summarize_transactions")(start_date="2026-03-01", end_date="2026-03-31")',
    ],
    aliases=[],
)
def summarize_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    settled_only: bool = True,
    include_pending: bool = False,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=settled_only,
        include_pending=include_pending,
        max_pages=max_pages,
    )
    summary = _summarize_flow(items)
    return _envelope(
        "starling.summarize_transactions",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "start_date": _isoformat(start_value),
            "end_date": _isoformat(end_value),
            "settled_only": settled_only,
            "include_pending": include_pending,
        },
        summary=summary,
        data={
            "transactions": items[: min(len(items), 250)],
            "top_counterparties": _top_counterparties(items),
        },
    )


@register_tool(
    namespace="starling",
    description="Summarize balances across Starling spending spaces and savings goals. The public API does not expose per-transaction space history.",
    examples=[
        'load_tool("starling.summarize_spending_by_space")()',
    ],
    aliases=[],
)
def summarize_spending_by_space(account_uid: Optional[str] = None) -> Dict[str, Any]:
    overview = get_spaces_overview(account_uid=account_uid)
    overview["operation"] = "starling.summarize_spending_by_space"
    overview["warnings"].append(
        "The public Starling personal API exposes current space balances but not per-transaction space allocations."
    )
    return overview


@register_tool(
    namespace="starling",
    description="Group Starling outflows by spending category over a date range.",
    examples=[
        'load_tool("starling.summarize_spending_by_category")(start_date="2026-03-01", end_date="2026-03-31")',
    ],
    aliases=[],
)
def summarize_spending_by_category(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=True,
        include_pending=False,
        max_pages=max_pages,
    )
    grouped: Dict[str, int] = defaultdict(int)
    for item in items:
        if item["direction"] == "OUT":
            grouped[item["spending_category"]] += item["outflow_minor_units"]
    ranked = sorted(grouped.items(), key=lambda pair: (-pair[1], pair[0]))
    currency = items[0]["currency"] if items else "GBP"
    return _envelope(
        "starling.summarize_spending_by_category",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "start_date": _isoformat(start_value),
            "end_date": _isoformat(end_value),
        },
        summary={
            "category_count": len(ranked),
            "outflow": _money(currency, sum(grouped.values())),
        },
        data={
            "categories": [
                {
                    "spending_category": category_name,
                    "currency": currency,
                    "outflow_minor_units": outflow_minor_units,
                }
                for category_name, outflow_minor_units in ranked[:TOP_ITEMS]
            ]
        },
    )


@register_tool(
    namespace="starling",
    description="Summarize cashflow inflows, outflows, and top counterparties from Starling feed data.",
    examples=[
        'load_tool("starling.summarize_cashflow")(start_date="2026-03-01", end_date="2026-03-31")',
    ],
    aliases=[],
)
def summarize_cashflow(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=True,
        include_pending=False,
        max_pages=max_pages,
    )
    flow = _summarize_flow(items)
    return _envelope(
        "starling.summarize_cashflow",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "start_date": _isoformat(start_value),
            "end_date": _isoformat(end_value),
        },
        summary=flow,
        data={
            "top_inflows": [
                item
                for item in sorted(
                    [candidate for candidate in items if candidate["direction"] == "IN"],
                    key=lambda candidate: (-candidate["inflow_minor_units"], candidate["event_time"] or ""),
                )[:TOP_ITEMS]
            ],
            "top_outflows": [
                item
                for item in sorted(
                    [candidate for candidate in items if candidate["direction"] == "OUT"],
                    key=lambda candidate: (-candidate["outflow_minor_units"], candidate["event_time"] or ""),
                )[:TOP_ITEMS]
            ],
            "top_counterparties": _top_counterparties(items),
        },
    )


@register_tool(
    namespace="starling",
    description="Compare two year-month periods in Starling by inflow, outflow, net, and top categories.",
    examples=[
        'load_tool("starling.compare_months")(month_a="2026-03", month_b="2026-02")',
    ],
    aliases=[],
)
def compare_months(
    month_a: str,
    month_b: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    if month_b is None:
        first_month_start, _ = _month_bounds(month_a)
        previous_month_end = first_month_start - timedelta(days=1)
        month_b = f"{previous_month_end.year:04d}-{previous_month_end.month:02d}"

    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_a, end_a = _month_bounds(month_a)
    start_b, end_b = _month_bounds(month_b)
    start_value = min(start_a, start_b)
    end_value = max(end_a, end_b)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=True,
        include_pending=False,
        max_pages=max_pages,
    )
    month_a_items = [item for item in items if item.get("event_date", "").startswith(month_a)]
    month_b_items = [item for item in items if item.get("event_date", "").startswith(month_b)]
    stats_a = _month_stats(month_a_items)
    stats_b = _month_stats(month_b_items)
    return _envelope(
        "starling.compare_months",
        inputs={
            "month_a": month_a,
            "month_b": month_b,
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
        },
        summary={
            "month_a_outflow": _money(stats_a["currency"], stats_a["outflow_minor_units"]),
            "month_b_outflow": _money(stats_b["currency"], stats_b["outflow_minor_units"]),
            "outflow_delta_minor_units": stats_a["outflow_minor_units"] - stats_b["outflow_minor_units"],
            "net_delta_minor_units": stats_a["net_minor_units"] - stats_b["net_minor_units"],
        },
        data={month_a: stats_a, month_b: stats_b},
    )


@register_tool(
    namespace="starling",
    description="Detect likely recurring Starling outflows such as subscriptions or regular bills.",
    examples=[
        'load_tool("starling.detect_recurring_outflows")()',
    ],
    aliases=[],
)
def detect_recurring_outflows(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    min_occurrences: int = 2,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date, default_days=120)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=True,
        include_pending=False,
        max_pages=max_pages,
    )
    recurring = _recurring_outflows(items, min_occurrences=min_occurrences)
    currency = recurring[0]["currency"] if recurring else "GBP"
    return _envelope(
        "starling.detect_recurring_outflows",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "start_date": _isoformat(start_value),
            "end_date": _isoformat(end_value),
            "min_occurrences": min_occurrences,
        },
        summary={
            "recurring_count": len(recurring),
            "projected_monthly_outflow": _money(
                currency,
                sum(candidate["typical_outflow_minor_units"] for candidate in recurring if candidate["cadence"] == "monthly"),
            ),
        },
        data={"recurring_outflows": recurring},
    )


@register_tool(
    namespace="starling",
    description="Detect unusually large or surprising Starling outflows relative to recent history.",
    examples=[
        'load_tool("starling.detect_unusual_transactions")()',
    ],
    aliases=[],
)
def detect_unusual_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    start_value, end_value = _coerce_range(start_date, end_date, default_days=120)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=start_value,
        end_value=end_value,
        settled_only=True,
        include_pending=False,
        max_pages=max_pages,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        if item["direction"] == "OUT":
            grouped[item["merchant_key"]].append(item)

    unusual: List[Dict[str, Any]] = []
    for merchant_key, group in grouped.items():
        ordered = sorted(group, key=lambda item: item.get("event_time") or "")
        if len(ordered) < 3:
            continue
        baseline = ordered[:-1]
        candidate = ordered[-1]
        baseline_amounts = [item["outflow_minor_units"] for item in baseline]
        baseline_median = int(round(float(median(baseline_amounts))))
        if baseline_median <= 0:
            continue
        if candidate["outflow_minor_units"] >= baseline_median * 2:
            unusual.append(
                {
                    "merchant_key": merchant_key,
                    "name": candidate["counterparty_name"] or candidate["reference"] or candidate["source"] or "Unknown",
                    "currency": candidate["currency"],
                    "candidate_outflow_minor_units": candidate["outflow_minor_units"],
                    "baseline_median_outflow_minor_units": baseline_median,
                    "ratio": _round2(candidate["outflow_minor_units"] / baseline_median),
                    "event_time": candidate["event_time"],
                    "feed_item_uid": candidate["feed_item_uid"],
                }
            )

    unusual.sort(key=lambda item: (-item["ratio"], -item["candidate_outflow_minor_units"], item["name"]))
    return _envelope(
        "starling.detect_unusual_transactions",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "start_date": _isoformat(start_value),
            "end_date": _isoformat(end_value),
        },
        summary={"unusual_count": len(unusual)},
        data={"transactions": unusual[:TOP_ITEMS]},
    )


@register_tool(
    namespace="starling",
    description="Forecast current-month Starling outflow using month-to-date settled spending.",
    examples=[
        'load_tool("starling.forecast_month_end_spend")()',
    ],
    aliases=[],
)
def forecast_month_end_spend(
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> Dict[str, Any]:
    now = _utc_now()
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    days_elapsed = max((now.date() - month_start.date()).days + 1, 1)
    days_in_month = calendar.monthrange(now.year, now.month)[1]

    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    items = _fetch_feed_items(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
        start_value=month_start,
        end_value=now,
        settled_only=True,
        include_pending=False,
        max_pages=max_pages,
    )
    outflow_minor_units = sum(item["outflow_minor_units"] for item in items)
    average_daily_outflow = _safe_ratio(outflow_minor_units, days_elapsed)
    forecast_outflow_minor_units = int(round(average_daily_outflow * days_in_month))
    currency = items[0]["currency"] if items else "GBP"
    return _envelope(
        "starling.forecast_month_end_spend",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "month": f"{now.year:04d}-{now.month:02d}",
        },
        summary={
            "month_to_date_outflow": _money(currency, outflow_minor_units),
            "forecast_outflow": _money(currency, forecast_outflow_minor_units),
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
        },
        derived={
            "average_daily_outflow_minor_units": int(round(average_daily_outflow)),
        },
    )


@register_tool(
    namespace="starling",
    description="Forecast the next 30 days of Starling inflows and outflows using recent history and recurring spend signals.",
    examples=[
        'load_tool("starling.forecast_next_30_days")()',
    ],
    aliases=[],
)
def forecast_next_30_days(
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    forecast = _forecast_next_30_days_data(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
    )
    return _envelope(
        "starling.forecast_next_30_days",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
        },
        summary={
            "projected_inflow": _money(forecast["currency"], forecast["projected_inflow_minor_units"]),
            "projected_outflow": _money(forecast["currency"], forecast["projected_outflow_minor_units"]),
            "projected_net": _money(forecast["currency"], forecast["projected_net_minor_units"]),
        },
        data={"recurring_due": forecast["recurring_due"]},
        derived={
            "recurring_outflow": _money(forecast["currency"], forecast["recurring_outflow_minor_units"]),
            "projected_discretionary_outflow": _money(
                forecast["currency"], forecast["projected_discretionary_outflow_minor_units"]
            ),
        },
    )


@register_tool(
    namespace="starling",
    description="Combine Starling balance and forecasted cashflow into a simple risk report for the next 30 days.",
    examples=[
        'load_tool("starling.get_cashflow_risk_report")()',
    ],
    aliases=[],
)
def get_cashflow_risk_report(
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    balance = client.get(f"accounts/{context['account_uid']}/balance") or {}
    forecast = _forecast_next_30_days_data(
        client,
        account_uid=context["account_uid"],
        category_uid=context["category_uid"],
    )
    effective_balance_minor_units = _minor_units(balance.get("effectiveBalance"))
    projected_end_minor_units = effective_balance_minor_units + forecast["projected_net_minor_units"]
    daily_burn_minor_units = max(
        int(round(_safe_ratio(forecast["projected_outflow_minor_units"] - forecast["projected_inflow_minor_units"], 30))),
        0,
    )
    days_of_cover = (
        int(_safe_ratio(effective_balance_minor_units, daily_burn_minor_units))
        if daily_burn_minor_units > 0
        else None
    )
    risk_level = "LOW"
    if projected_end_minor_units < 0:
        risk_level = "HIGH"
    elif days_of_cover is not None and days_of_cover < 14:
        risk_level = "MEDIUM"

    currency = _currency(balance.get("effectiveBalance"))
    return _envelope(
        "starling.get_cashflow_risk_report",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
        },
        summary={
            "risk_level": risk_level,
            "effective_balance": _money(currency, effective_balance_minor_units),
            "projected_end_balance": _money(currency, projected_end_minor_units),
            "days_of_cover": days_of_cover,
        },
        data={"balance": balance, "forecast": forecast},
    )


@register_tool(
    namespace="starling",
    description="Preview a Starling local payment without sending it.",
    examples=[
        'load_tool("starling.preview_local_payment")(body={"reference":"Rent","amount":{"currency":"GBP","minorUnits":50000}})',
    ],
    aliases=[],
)
def preview_local_payment(
    body: Dict[str, Any],
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    if not context["category_uid"]:
        raise StarlingValidationError("category_uid is required to preview a local payment")
    prepared_body = _prepare_payment_body(body, ensure_external_identifier=True)
    return _envelope(
        "starling.preview_local_payment",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "body": prepared_body,
        },
        summary={
            "reference": prepared_body.get("reference"),
            "amount": {
                "currency": _currency(prepared_body.get("amount")),
                "minor_units": _minor_units(prepared_body.get("amount")),
            },
        },
        actions=[
            {
                "type": "http_request",
                "method": "PUT",
                "endpoint": f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}",
                "body": prepared_body,
            }
        ],
    )


@register_tool(
    namespace="starling",
    description="Create a Starling local payment. Signed endpoint support must be configured in the shared client.",
    examples=[
        'load_tool("starling.create_local_payment")(body={"reference":"Rent","amount":{"currency":"GBP","minorUnits":50000}})',
    ],
    aliases=[],
)
def create_local_payment(
    body: Dict[str, Any],
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    if not context["category_uid"]:
        raise StarlingValidationError("category_uid is required to create a local payment")
    prepared_body = _prepare_payment_body(body, ensure_external_identifier=True)
    response = client.put(
        f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}",
        body=prepared_body,
    )
    return _envelope(
        "starling.create_local_payment",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "body": prepared_body,
        },
        summary={"payment_order_uid": (response or {}).get("paymentOrderUid")},
        data={"response": response},
    )


@register_tool(
    namespace="starling",
    description="Preview a Starling savings goal transfer without executing it.",
    examples=[
        'load_tool("starling.preview_savings_goal_transfer")(savings_goal_uid="...", direction="IN", amount_minor_units=5000)',
    ],
    aliases=[],
)
def preview_savings_goal_transfer(
    savings_goal_uid: str,
    direction: str,
    amount_minor_units: int,
    account_uid: Optional[str] = None,
    currency: str = "GBP",
    reference: Optional[str] = None,
    transfer_uid: Optional[str] = None,
) -> Dict[str, Any]:
    if direction not in {"IN", "OUT"}:
        raise StarlingValidationError('direction must be "IN" or "OUT"')
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    resolved_transfer_uid = transfer_uid or str(uuid4())
    endpoint = (
        f"account/{context['account_uid']}/savings-goals/{savings_goal_uid}/add-money/{resolved_transfer_uid}"
        if direction == "IN"
        else f"account/{context['account_uid']}/savings-goals/{savings_goal_uid}/withdraw-money/{resolved_transfer_uid}"
    )
    body = {
        "amount": {"currency": currency, "minorUnits": amount_minor_units},
        "reference": reference,
    }
    return _envelope(
        "starling.preview_savings_goal_transfer",
        inputs={
            "account_uid": context["account_uid"],
            "savings_goal_uid": savings_goal_uid,
            "direction": direction,
            "amount_minor_units": amount_minor_units,
            "currency": currency,
            "reference": reference,
            "transfer_uid": resolved_transfer_uid,
        },
        summary={"amount": _money(currency, amount_minor_units), "direction": direction},
        actions=[{"type": "http_request", "method": "PUT", "endpoint": endpoint, "body": body}],
    )


@register_tool(
    namespace="starling",
    description="Add money to a Starling savings goal using an immediate transfer.",
    examples=[
        'load_tool("starling.add_money_to_savings_goal")(savings_goal_uid="...", amount_minor_units=5000)',
    ],
    aliases=[],
)
def add_money_to_savings_goal(
    savings_goal_uid: str,
    amount_minor_units: int,
    account_uid: Optional[str] = None,
    currency: str = "GBP",
    reference: Optional[str] = None,
    transfer_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    resolved_transfer_uid = transfer_uid or str(uuid4())
    body = {"amount": {"currency": currency, "minorUnits": amount_minor_units}, "reference": reference}
    response = client.put(
        f"account/{context['account_uid']}/savings-goals/{savings_goal_uid}/add-money/{resolved_transfer_uid}",
        body=body,
    )
    return _envelope(
        "starling.add_money_to_savings_goal",
        inputs={
            "account_uid": context["account_uid"],
            "savings_goal_uid": savings_goal_uid,
            "amount_minor_units": amount_minor_units,
            "currency": currency,
            "reference": reference,
            "transfer_uid": resolved_transfer_uid,
        },
        summary={"transfer_uid": resolved_transfer_uid},
        data={"response": response},
    )


@register_tool(
    namespace="starling",
    description="Withdraw money from a Starling savings goal using an immediate transfer.",
    examples=[
        'load_tool("starling.withdraw_money_from_savings_goal")(savings_goal_uid="...", amount_minor_units=5000)',
    ],
    aliases=[],
)
def withdraw_money_from_savings_goal(
    savings_goal_uid: str,
    amount_minor_units: int,
    account_uid: Optional[str] = None,
    currency: str = "GBP",
    reference: Optional[str] = None,
    transfer_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=None)
    resolved_transfer_uid = transfer_uid or str(uuid4())
    body = {"amount": {"currency": currency, "minorUnits": amount_minor_units}, "reference": reference}
    response = client.put(
        f"account/{context['account_uid']}/savings-goals/{savings_goal_uid}/withdraw-money/{resolved_transfer_uid}",
        body=body,
    )
    return _envelope(
        "starling.withdraw_money_from_savings_goal",
        inputs={
            "account_uid": context["account_uid"],
            "savings_goal_uid": savings_goal_uid,
            "amount_minor_units": amount_minor_units,
            "currency": currency,
            "reference": reference,
            "transfer_uid": resolved_transfer_uid,
        },
        summary={"transfer_uid": resolved_transfer_uid},
        data={"response": response},
    )


@register_tool(
    namespace="starling",
    description="Preview a Starling standing order create or update call without executing it.",
    examples=[
        'load_tool("starling.preview_standing_order_change")(body={"reference":"Rent","amount":{"currency":"GBP","minorUnits":50000}})',
    ],
    aliases=[],
)
def preview_standing_order_change(
    body: Dict[str, Any],
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    payment_order_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    if not context["category_uid"]:
        raise StarlingValidationError("category_uid is required to preview a standing order change")
    prepared_body = _prepare_payment_body(body, ensure_external_identifier=payment_order_uid is None)
    if payment_order_uid:
        prepared_body["paymentOrderUid"] = payment_order_uid
        endpoint = (
            f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}"
            f"/standing-orders/{payment_order_uid}"
        )
    else:
        endpoint = (
            f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}"
            "/standing-orders"
        )
    return _envelope(
        "starling.preview_standing_order_change",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "payment_order_uid": payment_order_uid,
            "body": prepared_body,
        },
        summary={"reference": prepared_body.get("reference")},
        actions=[{"type": "http_request", "method": "PUT", "endpoint": endpoint, "body": prepared_body}],
    )


@register_tool(
    namespace="starling",
    description="Create or update a Starling standing order. Signed endpoint support must be configured in the shared client.",
    examples=[
        'load_tool("starling.create_or_update_standing_order")(body={"reference":"Rent","amount":{"currency":"GBP","minorUnits":50000}})',
    ],
    aliases=[],
)
def create_or_update_standing_order(
    body: Dict[str, Any],
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
    payment_order_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    if not context["category_uid"]:
        raise StarlingValidationError("category_uid is required to change a standing order")
    prepared_body = _prepare_payment_body(body, ensure_external_identifier=payment_order_uid is None)
    if payment_order_uid:
        prepared_body["paymentOrderUid"] = payment_order_uid
        endpoint = (
            f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}"
            f"/standing-orders/{payment_order_uid}"
        )
    else:
        endpoint = (
            f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}"
            "/standing-orders"
        )
    response = client.put(endpoint, body=prepared_body)
    return _envelope(
        "starling.create_or_update_standing_order",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "payment_order_uid": payment_order_uid,
            "body": prepared_body,
        },
        summary={"payment_order_uid": (response or {}).get("paymentOrderUid")},
        data={"response": response},
    )


@register_tool(
    namespace="starling",
    description="Cancel a Starling standing order. Signed endpoint support must be configured in the shared client.",
    examples=[
        'load_tool("starling.cancel_standing_order")(payment_order_uid="...")',
    ],
    aliases=[],
)
def cancel_standing_order(
    payment_order_uid: str,
    account_uid: Optional[str] = None,
    category_uid: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_client()
    context = _resolve_account_context(client, account_uid=account_uid, category_uid=category_uid)
    if not context["category_uid"]:
        raise StarlingValidationError("category_uid is required to cancel a standing order")
    endpoint = (
        f"payments/local/account/{context['account_uid']}/category/{context['category_uid']}"
        f"/standing-orders/{payment_order_uid}"
    )
    response = client.delete(endpoint)
    return _envelope(
        "starling.cancel_standing_order",
        inputs={
            "account_uid": context["account_uid"],
            "category_uid": context["category_uid"],
            "payment_order_uid": payment_order_uid,
        },
        summary={"cancelled": True},
        data={"response": response},
    )


@register_tool(
    namespace="starling",
    description="Preview Starling card control changes without applying them.",
    examples=[
        'load_tool("starling.preview_card_control_change")(card_uid="...", enabled=False)',
    ],
    aliases=[],
)
def preview_card_control_change(
    card_uid: str,
    enabled: Optional[bool] = None,
    atm_enabled: Optional[bool] = None,
    currency_switch_enabled: Optional[bool] = None,
    gambling_enabled: Optional[bool] = None,
    mag_stripe_enabled: Optional[bool] = None,
    mobile_wallet_enabled: Optional[bool] = None,
    online_enabled: Optional[bool] = None,
    pos_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    changes = _collect_card_control_changes(
        enabled=enabled,
        atm_enabled=atm_enabled,
        currency_switch_enabled=currency_switch_enabled,
        gambling_enabled=gambling_enabled,
        mag_stripe_enabled=mag_stripe_enabled,
        mobile_wallet_enabled=mobile_wallet_enabled,
        online_enabled=online_enabled,
        pos_enabled=pos_enabled,
    )
    if not changes:
        raise StarlingValidationError("At least one card control change must be supplied")
    return _envelope(
        "starling.preview_card_control_change",
        inputs={"card_uid": card_uid, "changes": changes},
        summary={"change_count": len(changes)},
        actions=[
            {
                "type": "http_request",
                "method": "PUT",
                "endpoint": f"cards/{card_uid}/{CARD_CONTROL_ENDPOINTS[name]}",
                "body": {"enabled": value},
            }
            for name, value in changes.items()
        ],
    )


@register_tool(
    namespace="starling",
    description="Update one or more Starling card controls for a card.",
    examples=[
        'load_tool("starling.update_card_controls")(card_uid="...", enabled=False)',
    ],
    aliases=[],
)
def update_card_controls(
    card_uid: str,
    enabled: Optional[bool] = None,
    atm_enabled: Optional[bool] = None,
    currency_switch_enabled: Optional[bool] = None,
    gambling_enabled: Optional[bool] = None,
    mag_stripe_enabled: Optional[bool] = None,
    mobile_wallet_enabled: Optional[bool] = None,
    online_enabled: Optional[bool] = None,
    pos_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    client = get_client()
    cards_payload = client.get("cards") or {}
    cards = [card for card in cards_payload.get("cards") or [] if isinstance(card, dict)]
    current_card = _find_card(cards, card_uid)
    changes = _collect_card_control_changes(
        enabled=enabled,
        atm_enabled=atm_enabled,
        currency_switch_enabled=currency_switch_enabled,
        gambling_enabled=gambling_enabled,
        mag_stripe_enabled=mag_stripe_enabled,
        mobile_wallet_enabled=mobile_wallet_enabled,
        online_enabled=online_enabled,
        pos_enabled=pos_enabled,
    )
    if not changes:
        raise StarlingValidationError("At least one card control change must be supplied")

    results: Dict[str, Any] = {}
    for control_name, value in changes.items():
        endpoint = f"cards/{card_uid}/{CARD_CONTROL_ENDPOINTS[control_name]}"
        results[control_name] = client.put(endpoint, body={"enabled": value})

    return _envelope(
        "starling.update_card_controls",
        inputs={"card_uid": card_uid, "changes": changes},
        summary={"change_count": len(changes)},
        data={"previous": current_card, "results": results},
    )


@register_tool(
    namespace="starling",
    description="Preview Starling payee creation and optional payee-account creation without executing them.",
    examples=[
        'load_tool("starling.preview_payee_create")(body={"payeeName":"Bob","payeeType":"INDIVIDUAL"})',
    ],
    aliases=[],
)
def preview_payee_create(
    body: Dict[str, Any],
    account_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    actions = [{"type": "http_request", "method": "PUT", "endpoint": "payees", "body": body}]
    if account_body:
        actions.append(
            {
                "type": "http_request",
                "method": "PUT",
                "endpoint": "payees/<payeeUid>/account",
                "body": account_body,
            }
        )
    return _envelope(
        "starling.preview_payee_create",
        inputs={"body": body, "account_body": account_body},
        summary={"creates_payee_account": bool(account_body)},
        actions=actions,
    )


@register_tool(
    namespace="starling",
    description="Create a Starling payee.",
    examples=[
        'load_tool("starling.create_payee")(body={"payeeName":"Bob","payeeType":"INDIVIDUAL"})',
    ],
    aliases=[],
)
def create_payee(body: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    response = client.put("payees", body=body)
    return _envelope(
        "starling.create_payee",
        inputs={"body": body},
        summary={"payee_uid": (response or {}).get("payeeUid")},
        data={"response": response},
    )


@register_tool(
    namespace="starling",
    description="Create an additional Starling account entry for an existing payee.",
    examples=[
        'load_tool("starling.create_payee_account")(payee_uid="...", body={"accountIdentifier":"12345678"})',
    ],
    aliases=[],
)
def create_payee_account(payee_uid: str, body: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    response = client.put(f"payees/{payee_uid}/account", body=body)
    return _envelope(
        "starling.create_payee_account",
        inputs={"payee_uid": payee_uid, "body": body},
        summary={"payee_account_uid": (response or {}).get("payeeAccountUid")},
        data={"response": response},
    )
