"""First-pass universe filters for the data thread."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class UniverseFilterConfig:
    exclude_st: bool = True
    exclude_suspended: bool = True
    min_listed_days: int = 120
    min_price: float | None = 1.0
    min_amount: float | None = None
    min_total_market_cap: float | None = None


@dataclass(frozen=True)
class FilterDecision:
    symbol: str
    market: str
    is_eligible: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def filter_universe(
    securities: Iterable[Mapping[str, Any]],
    valuation_snapshots: Iterable[Mapping[str, Any]] | None = None,
    config: UniverseFilterConfig | None = None,
    as_of: date | None = None,
) -> tuple[list[dict[str, Any]], list[FilterDecision]]:
    cfg = config or UniverseFilterConfig()
    valuation_by_key = _latest_valuations(valuation_snapshots or [])
    eligible: list[dict[str, Any]] = []
    decisions: list[FilterDecision] = []

    for security in securities:
        row = dict(security)
        key = (str(row.get("symbol", "")), str(row.get("market", "")))
        valuation = valuation_by_key.get(key, {})
        reasons = _exclusion_reasons(row, valuation, cfg, as_of)
        decision = FilterDecision(
            symbol=key[0],
            market=key[1],
            is_eligible=not reasons,
            reasons=tuple(reasons),
        )
        decisions.append(decision)
        if decision.is_eligible:
            eligible.append(row)
    return eligible, decisions


def _latest_valuations(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        record = dict(row)
        key = (str(record.get("symbol", "")), str(record.get("market", "")))
        if key == ("", ""):
            continue
        current = latest.get(key)
        if current is None:
            latest[key] = record
            continue
        if str(record.get("trade_date", "")) > str(current.get("trade_date", "")):
            latest[key] = record
    return latest


def _exclusion_reasons(
    security: Mapping[str, Any],
    valuation: Mapping[str, Any],
    config: UniverseFilterConfig,
    as_of: date | None,
) -> list[str]:
    reasons: list[str] = []
    status = str(security.get("status", "")).lower()
    if config.exclude_st and bool(security.get("is_st")):
        reasons.append("st_stock")
    if config.exclude_suspended and ("停牌" in status or "suspend" in status):
        reasons.append("suspended")
    if "退市" in status or "delist" in status:
        reasons.append("delisted")

    list_date = _as_date_or_none(security.get("list_date"))
    if as_of is not None and list_date is not None:
        listed_days = (as_of - list_date).days
        if listed_days < config.min_listed_days:
            reasons.append("new_listing")

    if config.min_price is not None:
        price = _to_float_or_none(valuation.get("last_price"))
        if price is not None and price < config.min_price:
            reasons.append("low_price")
    if config.min_amount is not None:
        amount = _to_float_or_none(valuation.get("amount"))
        if amount is not None and amount < config.min_amount:
            reasons.append("low_liquidity")
    if config.min_total_market_cap is not None:
        market_cap = _to_float_or_none(valuation.get("total_market_cap"))
        if market_cap is not None and market_cap < config.min_total_market_cap:
            reasons.append("small_market_cap")
    return reasons


def _as_date_or_none(value: Any) -> date | None:
    if value in ("", None):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _to_float_or_none(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
