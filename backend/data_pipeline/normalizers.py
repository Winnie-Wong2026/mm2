"""Normalize provider-native rows into project fields."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Iterable, Mapping

from .schemas import DailyBar, IndexBar, Security, TradeCalendarDay, ValuationSnapshot


def normalize_securities(
    rows: Iterable[Mapping[str, Any]],
    market: str,
    source: str = "akshare",
    source_function: str | None = None,
    ingested_at: datetime | None = None,
) -> list[dict[str, Any]]:
    timestamp = ingested_at or datetime.utcnow()
    normalized = []
    for row in rows:
        raw_symbol = str(_pick(row, "代码", "股票代码", "H股代码", default="")).strip()
        if not raw_symbol:
            continue
        symbol = normalize_symbol(raw_symbol, market)
        name = str(_pick(row, "名称", "中文名称", "股票简称", "A股名称", default="")).strip()
        security = Security(
            symbol=symbol,
            market=market,
            exchange=infer_exchange(symbol, market),
            name=name,
            raw_symbol=raw_symbol,
            status=_infer_status(row),
            is_st=_is_st(name),
            industry=_pick(row, "所属行业", "行业", default=None),
            source=source,
            source_function=str(row.get("source_function") or source_function or ""),
            ingested_at=timestamp,
        )
        normalized.append(security.to_dict())
    return normalized


def normalize_daily_bars(
    rows: Iterable[Mapping[str, Any]],
    market: str,
    symbol: str | None = None,
    adjust: str = "",
    source: str = "akshare",
    source_function: str | None = None,
    ingested_at: datetime | None = None,
) -> list[dict[str, Any]]:
    timestamp = ingested_at or datetime.utcnow()
    adjust_type = _normalize_adjust(adjust)
    normalized = []
    for row in rows:
        raw_symbol = str(_pick(row, "股票代码", "代码", "requested_symbol", default=symbol or "")).strip()
        canonical_symbol = normalize_symbol(raw_symbol or symbol or "", market)
        if not canonical_symbol:
            continue
        trade_date = _parse_date(_pick(row, "日期", "date", "trade_date"))
        open_price = _to_float(_pick(row, "开盘", "open"))
        high = _to_float(_pick(row, "最高", "high"))
        low = _to_float(_pick(row, "最低", "low"))
        close = _to_float(_pick(row, "收盘", "close"))
        bar = DailyBar(
            trade_date=trade_date,
            symbol=canonical_symbol,
            market=market,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=_normalize_volume(
                _pick(row, "成交量", "volume", default=None),
                market=market,
                source_function=str(row.get("source_function") or source_function or ""),
            ),
            volume_unit="share",
            source_volume_unit=_source_volume_unit(
                market=market,
                source_function=str(row.get("source_function") or source_function or ""),
            ),
            amount=_to_optional_float(_pick(row, "成交额", "amount", default=None)),
            turnover_rate=_to_optional_float(
                _pick(row, "换手率", "turnover_rate", "turnover", default=None)
            ),
            amplitude_pct=_to_optional_float(_pick(row, "振幅", "amplitude_pct", default=None)),
            pct_chg=_to_optional_float(_pick(row, "涨跌幅", "pct_chg", default=None)),
            change=_to_optional_float(_pick(row, "涨跌额", "change", default=None)),
            currency="CNY" if market == "cn" else "HKD",
            amount_currency="CNY" if market == "cn" else "HKD",
            adjust_type=adjust_type,
            is_suspended=_is_suspended(row),
            raw_symbol=raw_symbol,
            source=source,
            source_function=str(row.get("source_function") or source_function or ""),
            ingested_at=timestamp,
        )
        normalized.append(bar.to_dict())
    return normalized


def normalize_index_bars(
    rows: Iterable[Mapping[str, Any]],
    market: str,
    symbol: str,
    source: str = "akshare",
    source_function: str | None = None,
    ingested_at: datetime | None = None,
) -> list[dict[str, Any]]:
    timestamp = ingested_at or datetime.utcnow()
    normalized = []
    for row in rows:
        raw_symbol = str(_pick(row, "指数代码", "requested_symbol", "symbol", default=symbol)).strip()
        canonical_symbol = normalize_index_symbol(raw_symbol or symbol, market)
        if not canonical_symbol:
            continue
        bar = IndexBar(
            trade_date=_parse_date(_pick(row, "日期", "date", "trade_date")),
            symbol=canonical_symbol,
            market=market,
            open=_to_float(_pick(row, "开盘", "open")),
            high=_to_float(_pick(row, "最高", "high")),
            low=_to_float(_pick(row, "最低", "low")),
            close=_to_float(_pick(row, "收盘", "close")),
            volume=_to_optional_float(_pick(row, "成交量", "volume", default=None)),
            amount=_to_optional_float(_pick(row, "成交额", "成交金额", "amount", default=None)),
            turnover_rate=_to_optional_float(_pick(row, "换手率", "turnover_rate", default=None)),
            pct_chg=_to_optional_float(_pick(row, "涨跌幅", "pct_chg", default=None)),
            change=_to_optional_float(_pick(row, "涨跌额", "涨跌", "change", default=None)),
            currency="CNY" if market == "cn" else "HKD",
            amount_currency="CNY" if market == "cn" else "HKD",
            raw_symbol=raw_symbol,
            source=source,
            source_function=str(row.get("source_function") or source_function or ""),
            ingested_at=timestamp,
        )
        normalized.append(bar.to_dict())
    return normalized


def normalize_trade_calendar(
    rows: Iterable[Mapping[str, Any]],
    market: str = "cn",
    source: str = "akshare",
    source_function: str | None = None,
    ingested_at: datetime | None = None,
) -> list[dict[str, Any]]:
    timestamp = ingested_at or datetime.utcnow()
    normalized = []
    for row in rows:
        trade_date_value = _pick(row, "trade_date", "交易日", "日期", "calendar_date")
        if trade_date_value in ("", None):
            continue
        day = TradeCalendarDay(
            trade_date=_parse_date(trade_date_value),
            market=market,
            is_open=_to_bool(_pick(row, "is_open", "是否交易", default=True)),
            source=source,
            source_function=str(row.get("source_function") or source_function or ""),
            ingested_at=timestamp,
        )
        normalized.append(day.to_dict())
    return normalized


def normalize_valuation_snapshots(
    rows: Iterable[Mapping[str, Any]],
    market: str,
    source: str = "akshare",
    source_function: str | None = None,
    ingested_at: datetime | None = None,
) -> list[dict[str, Any]]:
    timestamp = ingested_at or datetime.utcnow()
    normalized = []
    for row in rows:
        raw_symbol = str(_pick(row, "代码", "股票代码", "H股代码", default="")).strip()
        if not raw_symbol:
            continue
        snapshot = ValuationSnapshot(
            trade_date=_parse_date(
                _pick(row, "日期", "日期时间", "trade_date", default=timestamp.date())
            ),
            symbol=normalize_symbol(raw_symbol, market),
            market=market,
            last_price=_to_optional_float(_pick(row, "最新价", "last_price", default=None)),
            pe_ttm=_to_optional_float(
                _pick(row, "市盈率-动态", "市盈率", "滚动市盈率", "pe_ttm", default=None)
            ),
            pb=_to_optional_float(_pick(row, "市净率", "pb", default=None)),
            dividend_yield=_to_optional_float(_pick(row, "股息率", "dividend_yield", default=None)),
            total_market_cap=_to_optional_float(
                _pick(row, "总市值", "total_market_cap", default=None)
            ),
            float_market_cap=_to_optional_float(
                _pick(row, "流通市值", "float_market_cap", default=None)
            ),
            amount=_to_optional_float(_pick(row, "成交额", "amount", default=None)),
            turnover_rate=_to_optional_float(_pick(row, "换手率", "turnover_rate", default=None)),
            currency="CNY" if market == "cn" else "HKD",
            amount_currency="CNY" if market == "cn" else "HKD",
            raw_symbol=raw_symbol,
            source=source,
            source_function=str(row.get("source_function") or source_function or ""),
            ingested_at=timestamp,
        )
        normalized.append(snapshot.to_dict())
    return normalized


def normalize_symbol(raw_symbol: str, market: str) -> str:
    raw = str(raw_symbol or "").strip().upper()
    if not raw:
        return ""
    if market == "cn" and raw.startswith(("SH", "SZ", "BJ")):
        return f"{raw[2:].zfill(6)}.{raw[:2]}"
    if "." in raw:
        code, suffix = raw.split(".", 1)
        if market == "hk":
            return f"{code.zfill(5)}.HK"
        return f"{code.zfill(6)}.{suffix}"
    if market == "hk":
        return f"{raw.zfill(5)}.HK"
    if market == "cn":
        exchange = infer_cn_exchange(raw)
        return f"{raw.zfill(6)}.{exchange.upper()}"
    return raw


def normalize_index_symbol(raw_symbol: str, market: str) -> str:
    raw = str(raw_symbol or "").strip().upper()
    if not raw:
        return ""
    if "." in raw:
        return raw
    if market == "cn" and raw.isdigit():
        return f"{raw.zfill(6)}.CN"
    if market == "hk":
        return f"{raw}.HK"
    return raw


def infer_exchange(symbol: str, market: str) -> str:
    if market == "hk":
        return "hkex"
    if market == "cn":
        return infer_cn_exchange(symbol.split(".")[0])
    return "unknown"


def infer_cn_exchange(code: str) -> str:
    clean = str(code).zfill(6)
    if clean.startswith(("5", "6", "9")):
        return "sh"
    if clean.startswith(("0", "1", "2", "3")):
        return "sz"
    if clean.startswith(("4", "8")):
        return "bj"
    return "unknown"


def _pick(row: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in ("", None):
            return row[key]
    return default


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    text = str(value)
    text = text.replace("/", "-")
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date()
    return datetime.fromisoformat(text[:10]).date()


def _to_float(value: Any) -> float:
    if value is None or value == "":
        raise ValueError("required numeric field is missing")
    result = _clean_float(value)
    if result is None:
        raise ValueError("required numeric field is missing")
    return result


def _to_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return _clean_float(value)


def _clean_float(value: Any) -> float | None:
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except TypeError:
        pass
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "--", "None", "nan", "NaN"}:
        return None
    if text.endswith("%"):
        text = text[:-1]
    try:
        result = float(text)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


def _normalize_volume(value: Any, market: str, source_function: str) -> float | None:
    volume = _to_optional_float(value)
    if volume is None:
        return None
    if _source_volume_unit(market, source_function) == "lot":
        return volume * 100
    return volume


def _source_volume_unit(market: str, source_function: str) -> str:
    if market == "cn" and source_function in {"", "stock_zh_a_hist"}:
        return "lot"
    return "share"


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"false", "0", "no", "n", "否", "休市"}:
        return False
    return True


def _normalize_adjust(adjust: str) -> str:
    if adjust == "qfq":
        return "qfq"
    if adjust == "hfq":
        return "hfq"
    return "none"


def _is_st(name: str) -> bool:
    normalized = name.upper()
    return "ST" in normalized


def _infer_status(row: Mapping[str, Any]) -> str:
    status = str(_pick(row, "状态", "status", default="")).strip()
    if status:
        return status
    return "active"


def _is_suspended(row: Mapping[str, Any]) -> bool:
    status = str(_pick(row, "状态", "status", default="")).strip()
    if "停牌" in status:
        return True
    volume = _to_optional_float(_pick(row, "成交量", "volume", default=None))
    amount = _to_optional_float(_pick(row, "成交额", "amount", default=None))
    return (volume == 0 and amount == 0)
