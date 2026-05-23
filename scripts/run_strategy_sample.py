from __future__ import annotations

import json
import math
import sys
from argparse import ArgumentParser
from pathlib import Path
from statistics import pstdev
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data_pipeline.storage import LocalDataStore
from backend.scoring import SimpleTopNScoringEngine
from backend.strategies.base import MacroAssessment, StrategyContext
from backend.strategies.registry import build_registry


STRATEGY_ID = "momentum_quality_daily"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def pct_return(first: float, last: float) -> float:
    if not first:
        return 0.0
    return (last / first - 1.0) * 100.0


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_from_return(value: float, multiplier: float) -> float:
    return round(clamp(50.0 + value * multiplier), 2)


def score_from_amount_change(value: float) -> float:
    return round(clamp(50.0 + value * 0.45), 2)


def score_from_liquidity(amount: float) -> float:
    if amount <= 0:
        return 55.0
    return round(clamp(52.0 + math.log10(amount / 50_000_000.0) * 11.0), 2)


def score_from_volatility(daily_returns: Iterable[float]) -> float:
    values = list(daily_returns)
    if len(values) < 2:
        return 35.0
    return round(clamp(20.0 + pstdev(values) * 12.0), 2)


def load_daily_groups(processed_root: Path) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    daily_root = processed_root / "daily_bars"
    for path in sorted(daily_root.glob("market=*/symbol=*/adjust=*/part.jsonl")):
        rows = sorted(read_jsonl(path), key=lambda item: item["trade_date"])
        if rows:
            groups.append(rows)
    return groups


def load_latest_valuations(processed_root: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    valuation_root = processed_root / "valuation_snapshots"
    for path in sorted(valuation_root.glob("market=*/part.jsonl")):
        for row in read_jsonl(path):
            symbol = str(row.get("symbol", "")).upper()
            if not symbol:
                continue
            existing = latest.get(symbol)
            if existing is None or str(row.get("trade_date", "")) >= str(existing.get("trade_date", "")):
                latest[symbol] = row
    return latest


def build_factor_records(processed_root: Path) -> list[dict[str, Any]]:
    daily_groups = load_daily_groups(processed_root)
    valuations = load_latest_valuations(processed_root)
    factor_records: list[dict[str, Any]] = []

    for rows in daily_groups:
        closes = [safe_float(row.get("close")) for row in rows if row.get("close") is not None]
        amounts = [safe_float(row.get("amount")) for row in rows if row.get("amount") is not None]
        if len(closes) < 2:
            continue

        first = rows[0]
        last = rows[-1]
        symbol = str(last["symbol"]).upper()
        market = str(last["market"])
        trade_date = str(last["trade_date"])
        return_full = pct_return(closes[0], closes[-1])
        return_half = pct_return(closes[max(0, len(closes) // 2 - 1)], closes[-1])
        previous_amount = sum(amounts[:-1]) / max(1, len(amounts) - 1)
        amount_change = (amounts[-1] / previous_amount - 1.0) * 100.0 if previous_amount else 0.0
        daily_returns = [
            pct_return(closes[index - 1], closes[index])
            for index in range(1, len(closes))
            if closes[index - 1]
        ]
        valuation = valuations.get(symbol, {})
        latest_amount = safe_float(valuation.get("amount"), amounts[-1] if amounts else 0.0)

        factor_payloads = {
            "momentum_20d": {
                "score": score_from_return(return_half, 2.2),
                "value": round(return_half, 4),
            },
            "momentum_60d": {
                "score": score_from_return(return_full, 1.6),
                "value": round(return_full, 4),
            },
            "quality_score": {
                "score": score_from_liquidity(latest_amount),
                "value": round(latest_amount, 2),
            },
            "amount_change_20d": {
                "score": score_from_amount_change(amount_change),
                "value": round(amount_change, 4),
            },
            "volatility_20d": {
                "score": score_from_volatility(daily_returns),
                "value": round(pstdev(daily_returns), 4) if len(daily_returns) >= 2 else 0.0,
            },
        }

        for factor_name, payload in factor_payloads.items():
            factor_records.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "market": market,
                    "factor_name": factor_name,
                    "factor_score": payload["score"],
                    "factor_value": payload["value"],
                    "window_start": str(first["trade_date"]),
                    "window_end": trade_date,
                    "source": "v0.2 local sample",
                }
            )

    return factor_records


def main() -> None:
    parser = ArgumentParser(description="Generate a local v0.2 strategy sample from processed data.")
    parser.add_argument("--processed-root", default="data/processed")
    parser.add_argument("--top-n", nargs="+", type=int, default=[20, 50])
    args = parser.parse_args()

    processed_root = Path(args.processed_root)
    factor_records = build_factor_records(processed_root)
    if not factor_records:
        raise SystemExit("No factor records generated. Run scripts/run_live_data_sample.py first.")

    trade_date = max(str(row["trade_date"]) for row in factor_records)
    registry = build_registry()
    strategy = registry.create(STRATEGY_ID)
    context = StrategyContext(
        trade_date=trade_date,
        frequency="daily",
        market_scope=("cn", "hk"),
        macro_assessment=MacroAssessment(
            as_of=trade_date,
            regime="v0.2 local sample",
            allow_stock_selection=True,
            confidence=72.0,
            summary="Local sample allows stock selection for strategy pipeline validation.",
        ),
    )
    signals = strategy.generate_signals(factor_records, context)
    ranking_outputs = SimpleTopNScoringEngine().build_rankings(
        signals,
        frequency="daily",
        top_n_values=args.top_n,
    )

    store = LocalDataStore(processed_root)
    factor_path = store.write_jsonl(
        factor_records,
        "factors",
        f"strategy_id={STRATEGY_ID}/frequency=daily",
    )
    signal_path = store.write_jsonl(
        [signal.to_dict() for signal in signals],
        "strategy_signals",
        f"strategy_id={STRATEGY_ID}/frequency=daily",
    )
    ranking_paths = [
        store.write_jsonl(
            [ranking.to_dict()],
            "rankings",
            (
                f"strategy_id={ranking.strategy_id}/frequency={ranking.frequency}/"
                f"market={ranking.market}/top_n={ranking.top_n}"
            ),
        )
        for ranking in ranking_outputs
    ]

    print(f"OK factors={len(factor_records)} path={factor_path}")
    print(f"OK signals={len(signals)} path={signal_path}")
    for path in ranking_paths:
        print(f"OK ranking={path}")


if __name__ == "__main__":
    main()
