"""Provider-neutral data source contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol


Record = dict[str, Any]


class DataSourceError(RuntimeError):
    """Base exception for data source failures."""


class DataSourceUnavailable(DataSourceError):
    """Raised when an optional provider dependency is not installed."""


class UnsupportedMarket(DataSourceError):
    """Raised when a provider cannot serve a requested market."""


@dataclass(frozen=True)
class DailyBarRequest:
    symbol: str
    market: str
    start_date: date
    end_date: date
    adjust: str = ""
    period: str = "daily"

    def start_yyyymmdd(self) -> str:
        return self.start_date.strftime("%Y%m%d")

    def end_yyyymmdd(self) -> str:
        return self.end_date.strftime("%Y%m%d")


@dataclass(frozen=True)
class IndexBarRequest:
    symbol: str
    market: str
    start_date: date
    end_date: date
    period: str = "daily"

    def start_yyyymmdd(self) -> str:
        return self.start_date.strftime("%Y%m%d")

    def end_yyyymmdd(self) -> str:
        return self.end_date.strftime("%Y%m%d")


class EquityDataSource(Protocol):
    source_name: str

    def fetch_universe(self, market: str) -> list[Record]:
        """Return provider-native security rows for a market."""

    def fetch_spot_snapshot(self, market: str) -> list[Record]:
        """Return provider-native latest snapshot rows for a market."""

    def fetch_daily_bars(self, request: DailyBarRequest) -> list[Record]:
        """Return provider-native daily bar rows for one symbol."""

    def fetch_index_bars(self, request: IndexBarRequest) -> list[Record]:
        """Return provider-native index bar rows for one benchmark index."""

    def fetch_trade_calendar(self, market: str = "cn") -> list[Record]:
        """Return provider-native trading calendar rows."""
