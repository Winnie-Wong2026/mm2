from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Sequence

from backend.strategies.signals import StrategySignal


@dataclass(frozen=True)
class RankingOutput:
    trade_date: str
    strategy_id: str
    frequency: str
    market: str
    top_n: int
    candidates: List[Dict[str, Any]]
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseScoringEngine(ABC):
    @abstractmethod
    def build_rankings(
        self,
        signals: Iterable[StrategySignal],
        frequency: str,
        top_n_values: Sequence[int],
    ) -> List[RankingOutput]:
        """Build market-specific ranking outputs from normalized strategy signals."""


class SimpleTopNScoringEngine(BaseScoringEngine):
    def build_rankings(
        self,
        signals: Iterable[StrategySignal],
        frequency: str,
        top_n_values: Sequence[int],
    ) -> List[RankingOutput]:
        signal_list = sorted(list(signals), key=lambda item: (item.market, item.rank))
        if not signal_list:
            return []

        outputs: List[RankingOutput] = []
        markets = sorted({signal.market for signal in signal_list})
        for market in markets:
            market_signals = [signal for signal in signal_list if signal.market == market]
            for top_n in sorted(set(int(value) for value in top_n_values)):
                selected = market_signals[:top_n]
                if not selected:
                    continue
                outputs.append(
                    RankingOutput(
                        trade_date=selected[0].trade_date,
                        strategy_id=selected[0].strategy_id,
                        frequency=frequency,
                        market=market,
                        top_n=top_n,
                        candidates=[signal.to_dict() for signal in selected],
                    )
                )
        return outputs

