from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping


MARKETS = {"cn", "hk"}
RISK_LEVELS = {"低", "中", "中高", "高"}


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def risk_level_from_score(risk_score: float) -> str:
    score = clamp_score(risk_score)
    if score < 30:
        return "低"
    if score < 55:
        return "中"
    if score < 75:
        return "中高"
    return "高"


@dataclass(frozen=True)
class FactorContribution:
    factor_name: str
    display_name: str = ""
    value: float = 0.0
    score: float = 50.0
    weight: float = 0.0
    direction: str = "positive"
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrategySignal:
    trade_date: str
    strategy_id: str
    symbol: str
    market: str
    score: float
    rank: int
    risk_score: float
    risk_level: str
    horizon: str
    reason_summary: str
    positive_factors: List[FactorContribution] = field(default_factory=list)
    negative_factors: List[FactorContribution] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.trade_date:
            raise ValueError("trade_date is required")
        if not self.strategy_id:
            raise ValueError("strategy_id is required")
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.market not in MARKETS:
            raise ValueError(f"market must be one of {sorted(MARKETS)}")
        if not 0 <= float(self.score) <= 100:
            raise ValueError("score must be between 0 and 100")
        if int(self.rank) < 1:
            raise ValueError("rank must be greater than 0")
        if not 0 <= float(self.risk_score) <= 100:
            raise ValueError("risk_score must be between 0 and 100")
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {sorted(RISK_LEVELS)}")
        if not self.horizon:
            raise ValueError("horizon is required")
        if not self.reason_summary:
            raise ValueError("reason_summary is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_date": self.trade_date,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "market": self.market,
            "score": self.score,
            "rank": self.rank,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "horizon": self.horizon,
            "reason_summary": self.reason_summary,
            "positive_factors": [item.to_dict() for item in self.positive_factors],
            "negative_factors": [item.to_dict() for item in self.negative_factors],
            "extra": dict(self.extra),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "StrategySignal":
        positive = [
            item if isinstance(item, FactorContribution) else FactorContribution(**dict(item))
            for item in data.get("positive_factors", [])
        ]
        negative = [
            item if isinstance(item, FactorContribution) else FactorContribution(**dict(item))
            for item in data.get("negative_factors", [])
        ]
        return cls(
            trade_date=str(data["trade_date"]),
            strategy_id=str(data["strategy_id"]),
            symbol=str(data["symbol"]),
            market=str(data["market"]),
            score=float(data["score"]),
            rank=int(data["rank"]),
            risk_score=float(data["risk_score"]),
            risk_level=str(data["risk_level"]),
            horizon=str(data["horizon"]),
            reason_summary=str(data["reason_summary"]),
            positive_factors=positive,
            negative_factors=negative,
            extra=dict(data.get("extra") or {}),
        )

