from __future__ import annotations

import sys
from argparse import ArgumentParser
from datetime import date
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data_pipeline import DataPipeline
from backend.data_sources import AkShareProvider


def main() -> None:
    parser = ArgumentParser(description="Run a small live external-data pull.")
    parser.add_argument(
        "--include-snapshots",
        action="store_true",
        help="Also pull full-market CN/HK spot snapshots. These external endpoints can be slow.",
    )
    args = parser.parse_args()

    pipeline = DataPipeline(AkShareProvider())
    jobs: list[tuple[str, Callable[[], object]]] = [
        (
            "A股日线 000001.SZ",
            lambda: pipeline.refresh_daily_bars(
                "000001.SZ",
                "cn",
                date(2024, 1, 2),
                date(2024, 1, 5),
            ),
        ),
        (
            "港股日线 00700.HK",
            lambda: pipeline.refresh_daily_bars(
                "00700.HK",
                "hk",
                date(2024, 1, 2),
                date(2024, 1, 5),
            ),
        ),
        ("A股交易日历", lambda: pipeline.refresh_trade_calendar("cn")),
        (
            "沪深300指数日线",
            lambda: pipeline.refresh_index_bars(
                "000300.CN",
                "cn",
                date(2024, 1, 2),
                date(2024, 1, 5),
            ),
        ),
    ]
    if args.include_snapshots:
        jobs.extend(
            [
                ("A股估值/快照", lambda: pipeline.refresh_valuation_snapshots("cn")),
                ("港股估值/快照", lambda: pipeline.refresh_valuation_snapshots("hk")),
            ]
        )

    failed = False
    for label, job in jobs:
        try:
            result = job()
        except Exception as exc:
            failed = True
            print(f"FAIL {label}: {type(exc).__name__}: {exc}")
            continue
        print(f"OK {label}: rows={result.row_count}")
        print(f"  raw={result.raw_path}")
        print(f"  processed={result.processed_path}")
        for issue in result.issues:
            print(f"  issue={issue.severity}:{issue.rule}:{issue.row_count}:{issue.message}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
