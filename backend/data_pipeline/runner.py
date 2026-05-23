"""Thin orchestration layer for data ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from backend.data_sources.base import DailyBarRequest, EquityDataSource, IndexBarRequest

from .normalizers import (
    normalize_daily_bars,
    normalize_index_bars,
    normalize_securities,
    normalize_trade_calendar,
    normalize_valuation_snapshots,
)
from .quality import QualityChecker, QualityIssue
from .storage import LocalDataStore


@dataclass(frozen=True)
class PipelineResult:
    dataset: str
    raw_path: Path | None
    processed_path: Path | None
    row_count: int
    issues: tuple[QualityIssue, ...]


class DataPipeline:
    def __init__(
        self,
        source: EquityDataSource,
        store: LocalDataStore | None = None,
        quality_checker: QualityChecker | None = None,
    ) -> None:
        self.source = source
        self.store = store or LocalDataStore()
        self.quality_checker = quality_checker or QualityChecker()

    def refresh_universe(self, market: str) -> PipelineResult:
        ingested_at = datetime.utcnow()
        raw_rows = self.source.fetch_universe(market)
        processed = normalize_securities(
            raw_rows,
            market=market,
            source=self.source.source_name,
            ingested_at=ingested_at,
        )
        issues = tuple(self.quality_checker.check_securities(processed))
        raw_path = self.store.write_jsonl(
            raw_rows,
            dataset="raw/securities",
            partition=f"market={market}",
        )
        processed_path = self.store.write_jsonl(
            processed,
            dataset="processed/securities",
            partition=f"market={market}",
        )
        return PipelineResult(
            dataset="securities",
            raw_path=raw_path,
            processed_path=processed_path,
            row_count=len(processed),
            issues=issues,
        )

    def refresh_valuation_snapshots(self, market: str) -> PipelineResult:
        ingested_at = datetime.utcnow()
        raw_rows = self.source.fetch_spot_snapshot(market)
        processed = normalize_valuation_snapshots(
            raw_rows,
            market=market,
            source=self.source.source_name,
            ingested_at=ingested_at,
        )
        issues = tuple(self.quality_checker.check_valuation_snapshots(processed))
        raw_path = self.store.write_jsonl(
            raw_rows,
            dataset="raw/valuation_snapshots",
            partition=f"market={market}",
        )
        processed_path = self.store.write_jsonl(
            processed,
            dataset="processed/valuation_snapshots",
            partition=f"market={market}",
        )
        return PipelineResult(
            dataset="valuation_snapshots",
            raw_path=raw_path,
            processed_path=processed_path,
            row_count=len(processed),
            issues=issues,
        )

    def refresh_daily_bars(
        self,
        symbol: str,
        market: str,
        start_date: date,
        end_date: date,
        adjust: str = "",
    ) -> PipelineResult:
        ingested_at = datetime.utcnow()
        request = DailyBarRequest(
            symbol=symbol,
            market=market,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        raw_rows = self.source.fetch_daily_bars(request)
        processed = normalize_daily_bars(
            raw_rows,
            market=market,
            symbol=symbol,
            adjust=adjust,
            source=self.source.source_name,
            ingested_at=ingested_at,
        )
        issues = tuple(self.quality_checker.check_daily_bars(processed))
        symbol_partition = symbol.replace(".", "_")
        adjust_partition = adjust or "none"
        partition = f"market={market}/symbol={symbol_partition}/adjust={adjust_partition}"
        raw_path = self.store.write_jsonl(raw_rows, dataset="raw/daily_bars", partition=partition)
        processed_path = self.store.write_jsonl(
            processed,
            dataset="processed/daily_bars",
            partition=partition,
        )
        return PipelineResult(
            dataset="daily_bars",
            raw_path=raw_path,
            processed_path=processed_path,
            row_count=len(processed),
            issues=issues,
        )

    def refresh_index_bars(
        self,
        symbol: str,
        market: str,
        start_date: date,
        end_date: date,
        period: str = "daily",
    ) -> PipelineResult:
        ingested_at = datetime.utcnow()
        request = IndexBarRequest(
            symbol=symbol,
            market=market,
            start_date=start_date,
            end_date=end_date,
            period=period,
        )
        raw_rows = self.source.fetch_index_bars(request)
        processed = normalize_index_bars(
            raw_rows,
            market=market,
            symbol=symbol,
            source=self.source.source_name,
            ingested_at=ingested_at,
        )
        issues = tuple(self.quality_checker.check_index_bars(processed))
        symbol_partition = symbol.replace(".", "_")
        partition = f"market={market}/symbol={symbol_partition}"
        raw_path = self.store.write_jsonl(raw_rows, dataset="raw/index_bars", partition=partition)
        processed_path = self.store.write_jsonl(
            processed,
            dataset="processed/index_bars",
            partition=partition,
        )
        return PipelineResult(
            dataset="index_bars",
            raw_path=raw_path,
            processed_path=processed_path,
            row_count=len(processed),
            issues=issues,
        )

    def refresh_trade_calendar(self, market: str = "cn") -> PipelineResult:
        ingested_at = datetime.utcnow()
        raw_rows = self.source.fetch_trade_calendar(market)
        processed = normalize_trade_calendar(
            raw_rows,
            market=market,
            source=self.source.source_name,
            ingested_at=ingested_at,
        )
        issues = tuple(self.quality_checker.check_trade_calendar(processed))
        raw_path = self.store.write_jsonl(
            raw_rows,
            dataset="raw/trade_calendar",
            partition=f"market={market}",
        )
        processed_path = self.store.write_jsonl(
            processed,
            dataset="processed/trade_calendar",
            partition=f"market={market}",
        )
        return PipelineResult(
            dataset="trade_calendar",
            raw_path=raw_path,
            processed_path=processed_path,
            row_count=len(processed),
            issues=issues,
        )
