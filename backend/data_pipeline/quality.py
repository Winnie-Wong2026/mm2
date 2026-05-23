"""Pure-Python data quality checks for normalized records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class QualityIssue:
    rule: str
    severity: str
    message: str
    row_count: int = 0
    samples: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QualityChecker:
    required_daily_fields = ("trade_date", "symbol", "market", "open", "high", "low", "close")
    required_security_fields = ("symbol", "market", "exchange")
    required_calendar_fields = ("trade_date", "market", "is_open")

    def check_daily_bars(
        self,
        rows: Iterable[Mapping[str, Any]],
        expected_latest_date: date | None = None,
    ) -> list[QualityIssue]:
        records = [dict(row) for row in rows]
        issues: list[QualityIssue] = []
        issues.extend(self._check_required_fields(records))
        issues.extend(self._check_duplicates(records))
        issues.extend(self._check_price_bounds(records))
        issues.extend(self._check_zero_liquidity(records))
        issues.extend(self._check_adjust_type(records))
        if expected_latest_date is not None:
            issues.extend(self._check_latest_date(records, expected_latest_date))
        return issues

    def check_index_bars(
        self,
        rows: Iterable[Mapping[str, Any]],
        expected_latest_date: date | None = None,
    ) -> list[QualityIssue]:
        records = [dict(row) for row in rows]
        issues: list[QualityIssue] = []
        issues.extend(
            self._check_required_fields(
                records,
                self.required_daily_fields,
                rule="required_index_fields",
                message="Required index bar fields are missing.",
            )
        )
        issues.extend(
            self._check_duplicates(
                records,
                key_fields=("trade_date", "symbol", "market"),
                rule="duplicate_index_key",
                message="Duplicate trade_date + symbol + market index keys found.",
            )
        )
        issues.extend(self._check_price_bounds(records))
        if expected_latest_date is not None:
            issues.extend(self._check_latest_date(records, expected_latest_date))
        return issues

    def check_securities(self, rows: Iterable[Mapping[str, Any]]) -> list[QualityIssue]:
        records = [dict(row) for row in rows]
        issues: list[QualityIssue] = []
        issues.extend(
            self._check_required_fields(
                records,
                self.required_security_fields,
                rule="required_security_fields",
                message="Required security master fields are missing.",
            )
        )
        issues.extend(
            self._check_duplicates(
                records,
                key_fields=("symbol", "market"),
                rule="duplicate_security_key",
                message="Duplicate symbol + market security keys found.",
            )
        )
        missing_names = [_row_id(row) for row in records if row.get("name") in ("", None)]
        if missing_names:
            issues.append(
                QualityIssue(
                    rule="missing_security_name",
                    severity="warning",
                    message="Security master rows are missing stock names.",
                    row_count=len(missing_names),
                    samples=tuple(missing_names[:5]),
                )
            )
        return issues

    def check_trade_calendar(self, rows: Iterable[Mapping[str, Any]]) -> list[QualityIssue]:
        records = [dict(row) for row in rows]
        issues: list[QualityIssue] = []
        issues.extend(
            self._check_required_fields(
                records,
                self.required_calendar_fields,
                rule="required_calendar_fields",
                message="Required trade calendar fields are missing.",
            )
        )
        issues.extend(
            self._check_duplicates(
                records,
                key_fields=("trade_date", "market"),
                rule="duplicate_calendar_key",
                message="Duplicate trade_date + market calendar keys found.",
            )
        )
        if not records:
            issues.append(
                QualityIssue(
                    rule="empty_trade_calendar",
                    severity="error",
                    message="Trade calendar contains no rows.",
                )
            )
        return issues

    def check_valuation_snapshots(self, rows: Iterable[Mapping[str, Any]]) -> list[QualityIssue]:
        records = [dict(row) for row in rows]
        issues: list[QualityIssue] = []
        issues.extend(
            self._check_required_fields(
                records,
                ("trade_date", "symbol", "market"),
                rule="required_valuation_fields",
                message="Required valuation snapshot fields are missing.",
            )
        )
        issues.extend(
            self._check_duplicates(
                records,
                key_fields=("trade_date", "symbol", "market"),
                rule="duplicate_valuation_key",
                message="Duplicate trade_date + symbol + market valuation keys found.",
            )
        )
        missing_metrics = [
            _row_id(row)
            for row in records
            if all(row.get(field) in ("", None) for field in ("pe_ttm", "pb", "total_market_cap"))
        ]
        if missing_metrics:
            issues.append(
                QualityIssue(
                    rule="missing_valuation_metrics",
                    severity="warning",
                    message="Rows are missing pe_ttm, pb, and total_market_cap.",
                    row_count=len(missing_metrics),
                    samples=tuple(missing_metrics[:5]),
                )
            )
        return issues

    def _check_required_fields(
        self,
        records: list[dict[str, Any]],
        fields: tuple[str, ...] | None = None,
        rule: str = "required_daily_fields",
        message: str = "Required daily bar fields are missing.",
    ) -> list[QualityIssue]:
        fields = fields or self.required_daily_fields
        bad = []
        for row in records:
            if any(row.get(field) in ("", None) for field in fields):
                bad.append(_row_id(row))
        if not bad:
            return []
        return [
            QualityIssue(
                rule=rule,
                severity="error",
                message=message,
                row_count=len(bad),
                samples=tuple(bad[:5]),
            )
        ]

    def _check_duplicates(
        self,
        records: list[dict[str, Any]],
        key_fields: tuple[str, ...] = ("trade_date", "symbol", "market", "adjust_type"),
        rule: str = "duplicate_daily_key",
        message: str = "Duplicate trade_date + symbol + market + adjust_type keys found.",
    ) -> list[QualityIssue]:
        seen = set()
        duplicates = []
        for row in records:
            key = tuple(row.get(field) for field in key_fields)
            if key in seen:
                duplicates.append(_row_id(row))
            seen.add(key)
        if not duplicates:
            return []
        return [
            QualityIssue(
                rule=rule,
                severity="error",
                message=message,
                row_count=len(duplicates),
                samples=tuple(duplicates[:5]),
            )
        ]

    def _check_price_bounds(self, records: list[dict[str, Any]]) -> list[QualityIssue]:
        bad = []
        for row in records:
            try:
                open_price = float(row["open"])
                high = float(row["high"])
                low = float(row["low"])
                close = float(row["close"])
            except (KeyError, TypeError, ValueError):
                continue
            if min(open_price, high, low, close) <= 0:
                bad.append(_row_id(row))
                continue
            if high < low or high < max(open_price, close) or low > min(open_price, close):
                bad.append(_row_id(row))
        if not bad:
            return []
        return [
            QualityIssue(
                rule="daily_price_bounds",
                severity="error",
                message="OHLC prices are non-positive or internally inconsistent.",
                row_count=len(bad),
                samples=tuple(bad[:5]),
            )
        ]

    def _check_zero_liquidity(self, records: list[dict[str, Any]]) -> list[QualityIssue]:
        bad = []
        for row in records:
            volume = _to_float_or_none(row.get("volume"))
            amount = _to_float_or_none(row.get("amount"))
            if volume == 0 or amount == 0:
                bad.append(_row_id(row))
        if not bad:
            return []
        return [
            QualityIssue(
                rule="zero_liquidity",
                severity="warning",
                message="Volume or amount is zero; this may indicate suspension or illiquidity.",
                row_count=len(bad),
                samples=tuple(bad[:5]),
            )
        ]

    def _check_adjust_type(self, records: list[dict[str, Any]]) -> list[QualityIssue]:
        adjust_types = {row.get("adjust_type") for row in records if row.get("adjust_type")}
        if len(adjust_types) <= 1:
            return []
        return [
            QualityIssue(
                rule="mixed_adjust_type",
                severity="error",
                message="A single daily bar batch contains mixed adjustment types.",
                row_count=len(records),
                samples=tuple(sorted(str(item) for item in adjust_types)),
            )
        ]

    def _check_latest_date(
        self,
        records: list[dict[str, Any]],
        expected_latest_date: date,
    ) -> list[QualityIssue]:
        trade_dates = [row.get("trade_date") for row in records if row.get("trade_date")]
        if not trade_dates:
            return [
                QualityIssue(
                    rule="latest_trade_date",
                    severity="error",
                    message="No trade_date values found.",
                )
            ]
        latest = max(_as_date(item) for item in trade_dates)
        if latest >= expected_latest_date:
            return []
        return [
            QualityIssue(
                rule="latest_trade_date",
                severity="warning",
                message=(
                    f"Latest trade_date {latest.isoformat()} is older than "
                    f"expected {expected_latest_date.isoformat()}."
                ),
                row_count=len(records),
            )
        ]


def _row_id(row: Mapping[str, Any]) -> str:
    return f"{row.get('market', '?')}:{row.get('symbol', '?')}:{row.get('trade_date', '?')}"


def _to_float_or_none(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])
