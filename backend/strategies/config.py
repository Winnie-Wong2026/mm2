from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional


SUPPORTED_MARKETS = {"cn", "hk"}
SUPPORTED_FREQUENCIES = {"daily", "weekly"}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


@dataclass(frozen=True)
class StrategyConfig:
    strategy_id: str
    name: str
    markets: List[str]
    frequency: str
    universe: str
    factors: List[str]
    model: Dict[str, Any]
    horizons: List[str]
    rebalance_rule: str
    risk_rule: Dict[str, Any]
    explanation_template: str
    entrypoint_module: str
    entrypoint_class: str
    version: str = "0.1.0"
    description: str = ""
    enabled: bool = True
    output_top_n: List[int] = field(default_factory=lambda: [20, 50])
    tags: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "StrategyConfig":
        entrypoint = data.get("entrypoint") or {}
        markets = [str(item) for item in _as_list(data.get("market"))]
        horizons = [str(item) for item in _as_list(data.get("horizon"))]
        factors = [str(item) for item in _as_list(data.get("factors"))]

        config = cls(
            strategy_id=str(data.get("strategy_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            markets=markets,
            frequency=str(data.get("frequency", "")).strip(),
            universe=str(data.get("universe", "")).strip(),
            factors=factors,
            model=dict(data.get("model") or {}),
            horizons=horizons,
            rebalance_rule=str(data.get("rebalance_rule", "")).strip(),
            risk_rule=dict(data.get("risk_rule") or {}),
            explanation_template=str(data.get("explanation_template", "")).strip(),
            entrypoint_module=str(entrypoint.get("module", "")).strip(),
            entrypoint_class=str(entrypoint.get("class", "")).strip(),
            version=str(data.get("version", "0.1.0")).strip(),
            description=str(data.get("description", "")).strip(),
            enabled=bool(data.get("enabled", True)),
            output_top_n=[int(item) for item in _as_list(data.get("output_top_n") or [20, 50])],
            tags=[str(item) for item in _as_list(data.get("tags"))],
            raw=dict(data),
        )
        config.validate()
        return config

    def validate(self) -> None:
        missing = []
        required = {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "market": self.markets,
            "frequency": self.frequency,
            "universe": self.universe,
            "factors": self.factors,
            "model": self.model,
            "horizon": self.horizons,
            "rebalance_rule": self.rebalance_rule,
            "risk_rule": self.risk_rule,
            "explanation_template": self.explanation_template,
            "entrypoint.module": self.entrypoint_module,
            "entrypoint.class": self.entrypoint_class,
        }
        for key, value in required.items():
            if not value:
                missing.append(key)
        if missing:
            raise ValueError(f"Missing strategy config fields: {', '.join(missing)}")

        unknown_markets = set(self.markets) - SUPPORTED_MARKETS
        if unknown_markets:
            raise ValueError(f"Unsupported markets: {sorted(unknown_markets)}")

        if self.frequency not in SUPPORTED_FREQUENCIES:
            raise ValueError(f"Unsupported frequency: {self.frequency}")

        if min(self.output_top_n) <= 0:
            raise ValueError("output_top_n values must be positive")

    def requires_factor(self, factor_name: str) -> bool:
        return factor_name in self.factors

    def primary_horizon(self) -> str:
        return self.horizons[-1] if self.horizons else ""

    def enabled_for_market(self, market: str) -> bool:
        return market in self.markets

    def missing_factors(self, available_factors: Iterable[str]) -> List[str]:
        available = set(available_factors)
        return [factor_name for factor_name in self.factors if factor_name not in available]

