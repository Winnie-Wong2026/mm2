from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from backend.data_pipeline import DataPipeline, LocalDataStore


class FakeSource:
    source_name = "fake"

    def fetch_universe(self, market: str) -> list[dict]:
        return [
            {
                "代码": "000001",
                "名称": "平安银行",
                "source_function": "stock_zh_a_spot_em",
            }
        ]

    def fetch_spot_snapshot(self, market: str) -> list[dict]:
        return [
            {
                "代码": "000001",
                "名称": "平安银行",
                "最新价": "12.3",
                "市盈率-动态": "8.5",
                "市净率": "0.8",
                "总市值": "238000000000",
                "成交额": "1200000000",
                "source_function": "stock_zh_a_spot_em",
            }
        ]

    def fetch_daily_bars(self, request) -> list[dict]:
        return [
            {
                "日期": "2026-05-22",
                "股票代码": request.symbol.split(".")[0],
                "开盘": "12.0",
                "最高": "12.5",
                "最低": "11.9",
                "收盘": "12.3",
                "成交量": "10",
                "成交额": "123000",
                "source_function": "stock_zh_a_hist",
            }
        ]

    def fetch_index_bars(self, request) -> list[dict]:
        return [
            {
                "日期": "2026-05-22",
                "开盘": "3900",
                "最高": "3950",
                "最低": "3880",
                "收盘": "3920",
                "成交量": "100000",
                "成交额": "200000000",
                "source_function": "index_zh_a_hist",
                "requested_symbol": request.symbol,
            }
        ]

    def fetch_trade_calendar(self, market: str = "cn") -> list[dict]:
        return [{"trade_date": "2026-05-22", "source_function": "tool_trade_date_hist_sina"}]


class DataPipelineTest(unittest.TestCase):
    def test_refreshes_first_round_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = DataPipeline(FakeSource(), store=LocalDataStore(tmp_dir))

            universe = pipeline.refresh_universe("cn")
            valuations = pipeline.refresh_valuation_snapshots("cn")
            bars = pipeline.refresh_daily_bars(
                "000001.SZ",
                "cn",
                start_date=date(2026, 5, 20),
                end_date=date(2026, 5, 22),
            )
            index_bars = pipeline.refresh_index_bars(
                "000300.CN",
                "cn",
                start_date=date(2026, 5, 20),
                end_date=date(2026, 5, 22),
            )
            calendar = pipeline.refresh_trade_calendar("cn")

            self.assertEqual(universe.row_count, 1)
            self.assertEqual(valuations.row_count, 1)
            self.assertEqual(bars.row_count, 1)
            self.assertEqual(index_bars.row_count, 1)
            self.assertEqual(calendar.row_count, 1)
            self.assertEqual(bars.issues, ())

            daily_path = (
                Path(tmp_dir)
                / "processed/daily_bars/market=cn/symbol=000001_SZ/adjust=none/part.jsonl"
            )
            daily_row = json.loads(daily_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(daily_row["volume"], 1000.0)
            self.assertEqual(daily_row["volume_unit"], "share")
            self.assertEqual(daily_row["source_volume_unit"], "lot")


if __name__ == "__main__":
    unittest.main()
