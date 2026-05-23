"""AkShare-backed market data provider.

The dependency is imported lazily so the rest of the data pipeline remains
importable in a clean local environment.
"""

from __future__ import annotations

import importlib
import time
from datetime import date, datetime
from typing import Any, Callable

from .base import DailyBarRequest, DataSourceUnavailable, IndexBarRequest, Record, UnsupportedMarket


class AkShareProvider:
    source_name = "akshare"

    def __init__(self, ak_module: Any | None = None) -> None:
        self._ak = ak_module

    def _module(self) -> Any:
        if self._ak is not None:
            return self._ak
        try:
            self._ak = importlib.import_module("akshare")
        except ModuleNotFoundError as exc:
            raise DataSourceUnavailable(
                "AkShare is not installed. Install akshare with the project dependency manager "
                "before running live data downloads."
            ) from exc
        return self._ak

    def fetch_universe(self, market: str) -> list[Record]:
        return self.fetch_spot_snapshot(market)

    def fetch_spot_snapshot(self, market: str) -> list[Record]:
        ak = self._module()
        normalized_market = market.lower()
        if normalized_market == "cn":
            try:
                rows = _to_records(_call_with_retries(ak.stock_zh_a_spot_em))
                return _with_source(rows, "stock_zh_a_spot_em")
            except Exception:
                rows = _to_records(_call_with_retries(ak.stock_zh_a_spot))
                return _with_source(rows, "stock_zh_a_spot")
        if normalized_market == "hk":
            try:
                rows = _to_records(_call_with_retries(ak.stock_hk_spot_em))
                return _with_source(rows, "stock_hk_spot_em")
            except Exception:
                rows = _to_records(_call_with_retries(ak.stock_hk_spot))
                return _with_source(rows, "stock_hk_spot")
        if normalized_market == "hk_connect":
            rows = []
            for function_name in ("stock_hsgt_sh_hk_spot_em", "stock_hsgt_sz_hk_spot_em"):
                if not hasattr(ak, function_name):
                    continue
                function = getattr(ak, function_name)
                for row in _to_records(function()):
                    row["source_function"] = function_name
                    rows.append(row)
            return _dedupe_by_code(rows)
        raise UnsupportedMarket(f"AkShareProvider does not support market={market!r}")

    def fetch_daily_bars(self, request: DailyBarRequest) -> list[Record]:
        ak = self._module()
        market = request.market.lower()
        symbol = _provider_symbol(request.symbol, market)
        if market == "cn":
            try:
                frame = _call_with_retries(
                    ak.stock_zh_a_hist,
                    symbol=symbol,
                    period=request.period,
                    start_date=request.start_yyyymmdd(),
                    end_date=request.end_yyyymmdd(),
                    adjust=request.adjust,
                )
                rows = _to_records(frame)
                return _with_source(rows, "stock_zh_a_hist", symbol)
            except Exception:
                provider_symbol = _provider_cn_stock_symbol(symbol)
                frame = _call_with_retries(
                    ak.stock_zh_a_daily,
                    symbol=provider_symbol,
                    start_date=request.start_yyyymmdd(),
                    end_date=request.end_yyyymmdd(),
                    adjust=request.adjust,
                )
                rows = _to_records(frame)
                return _with_source(rows, "stock_zh_a_daily", symbol)
        if market == "hk":
            try:
                frame = _call_with_retries(
                    ak.stock_hk_hist,
                    symbol=symbol,
                    period=request.period,
                    start_date=request.start_yyyymmdd(),
                    end_date=request.end_yyyymmdd(),
                    adjust=request.adjust,
                )
                rows = _to_records(frame)
                return _with_source(rows, "stock_hk_hist", symbol)
            except Exception:
                frame = _call_with_retries(ak.stock_hk_daily, symbol=symbol, adjust=request.adjust)
                rows = _filter_rows_by_date(_to_records(frame), request.start_date, request.end_date)
                return _with_source(rows, "stock_hk_daily", symbol)
        raise UnsupportedMarket(f"AkShareProvider does not support market={request.market!r}")

    def fetch_index_bars(self, request: IndexBarRequest) -> list[Record]:
        ak = self._module()
        market = request.market.lower()
        symbol = _provider_index_symbol(request.symbol, market)
        if market == "cn":
            try:
                frame = _call_with_retries(
                    ak.index_zh_a_hist,
                    symbol=symbol,
                    period=request.period,
                    start_date=request.start_yyyymmdd(),
                    end_date=request.end_yyyymmdd(),
                )
                rows = _to_records(frame)
                return _with_source(rows, "index_zh_a_hist", symbol)
            except Exception:
                provider_symbol = _provider_cn_index_symbol(symbol)
                frame = _call_with_retries(
                    ak.stock_zh_index_daily_tx,
                    symbol=provider_symbol,
                    start_date=request.start_yyyymmdd(),
                    end_date=request.end_yyyymmdd(),
                )
                rows = _to_records(frame)
                return _with_source(rows, "stock_zh_index_daily_tx", symbol)
        raise UnsupportedMarket(
            "AkShareProvider currently only exposes daily index bars for market='cn'. "
            "Add a dedicated HK history source before relying on HK benchmarks."
        )

    def fetch_trade_calendar(self, market: str = "cn") -> list[Record]:
        if market.lower() != "cn":
            raise UnsupportedMarket("AkShareProvider currently only exposes the A-share calendar")
        ak = self._module()
        rows = _to_records(_call_with_retries(ak.tool_trade_date_hist_sina))
        return _with_source(rows, "tool_trade_date_hist_sina")


def _to_records(frame: Any) -> list[Record]:
    if frame is None:
        return []
    if hasattr(frame, "to_dict"):
        return [dict(row) for row in frame.to_dict("records")]
    if isinstance(frame, list):
        return [dict(row) for row in frame]
    raise TypeError(f"Unsupported frame type: {type(frame)!r}")


def _call_with_retries(function: Callable[..., Any], *args: Any, retries: int = 2, **kwargs: Any) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return function(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def _with_source(
    rows: list[Record],
    function_name: str,
    requested_symbol: str | None = None,
) -> list[Record]:
    for row in rows:
        row.setdefault("source_function", function_name)
        if requested_symbol is not None:
            row.setdefault("requested_symbol", requested_symbol)
    return rows


def _dedupe_by_code(rows: list[Record]) -> list[Record]:
    seen = set()
    deduped: list[Record] = []
    for row in rows:
        code = row.get("代码") or row.get("股票代码") or row.get("H股代码")
        if code in seen:
            continue
        seen.add(code)
        deduped.append(row)
    return deduped


def _filter_rows_by_date(rows: list[Record], start_date: date, end_date: date) -> list[Record]:
    filtered = []
    for row in rows:
        row_date = _parse_row_date(row)
        if row_date is None or start_date <= row_date <= end_date:
            filtered.append(row)
    return filtered


def _parse_row_date(row: Record) -> date | None:
    value = row.get("日期") or row.get("date") or row.get("trade_date")
    if value in ("", None):
        return None
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date()
    return date.fromisoformat(text)


def _provider_symbol(symbol: str, market: str) -> str:
    raw = symbol.strip().upper()
    if market == "cn":
        return raw.split(".")[0]
    if market == "hk":
        return raw.split(".")[0].zfill(5)
    return raw


def _provider_index_symbol(symbol: str, market: str) -> str:
    raw = symbol.strip().upper()
    if "." in raw:
        raw = raw.split(".", 1)[0]
    if market == "cn" and raw.startswith(("SH", "SZ", "BJ")):
        raw = raw[2:]
    return raw.zfill(6) if market == "cn" and raw.isdigit() else raw


def _provider_cn_stock_symbol(symbol: str) -> str:
    raw = symbol.strip().upper()
    if "." in raw:
        code, suffix = raw.split(".", 1)
        return f"{suffix.lower()}{code.zfill(6)}"
    code = raw.zfill(6)
    if code.startswith(("5", "6", "9")):
        return f"sh{code}"
    if code.startswith(("4", "8")):
        return f"bj{code}"
    return f"sz{code}"


def _provider_cn_index_symbol(symbol: str) -> str:
    raw = symbol.strip().upper()
    if "." in raw:
        raw = raw.split(".", 1)[0]
    code = raw[-6:] if raw[-6:].isdigit() else raw
    if code.startswith(("399", "159")):
        return f"sz{code}"
    return f"sh{code}"
