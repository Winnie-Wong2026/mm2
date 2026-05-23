"""Canonical data records used by the data thread."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class Security:
    symbol: str
    market: str
    exchange: str
    name: str
    raw_symbol: str
    list_date: date | None = None
    status: str = "unknown"
    is_st: bool = False
    industry: str | None = None
    source: str = "akshare"
    source_function: str | None = None
    ingested_at: datetime | None = None
    data_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DailyBar:
    trade_date: date
    symbol: str
    market: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    volume_unit: str = "share"
    source_volume_unit: str | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    adj_factor: float | None = None
    amplitude_pct: float | None = None
    pct_chg: float | None = None
    change: float | None = None
    currency: str | None = None
    amount_currency: str | None = None
    adjust_type: str = "none"
    is_suspended: bool = False
    raw_symbol: str | None = None
    source: str = "akshare"
    source_function: str | None = None
    ingested_at: datetime | None = None
    data_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IndexBar:
    trade_date: date
    symbol: str
    market: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    pct_chg: float | None = None
    change: float | None = None
    currency: str | None = None
    amount_currency: str | None = None
    raw_symbol: str | None = None
    source: str = "akshare"
    source_function: str | None = None
    ingested_at: datetime | None = None
    data_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradeCalendarDay:
    trade_date: date
    market: str
    is_open: bool = True
    source: str = "akshare"
    source_function: str | None = None
    ingested_at: datetime | None = None
    data_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValuationSnapshot:
    trade_date: date
    symbol: str
    market: str
    last_price: float | None = None
    pe_ttm: float | None = None
    pb: float | None = None
    dividend_yield: float | None = None
    total_market_cap: float | None = None
    float_market_cap: float | None = None
    amount: float | None = None
    turnover_rate: float | None = None
    currency: str | None = None
    amount_currency: str | None = None
    raw_symbol: str | None = None
    source: str = "akshare"
    source_function: str | None = None
    ingested_at: datetime | None = None
    data_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
