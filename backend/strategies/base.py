from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .config import StrategyConfig
from .signals import StrategySignal


@dataclass(frozen=True)
class MacroAssessment:
    as_of: str
    regime: str
    allow_stock_selection: bool
    confidence: float = 0.0
    summary: str = ""
    risk_notes: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class SectorAllocation:
    sector: str
    stance: str
    target_weight: float
    reason: str = ""
    risk_note: str = ""


@dataclass(frozen=True)
class PositionGuidance:
    gross_position_range: str
    single_stock_limit: str
    cash_buffer: str
    rebalance_note: str = ""


@dataclass(frozen=True)
class StrategyContext:
    trade_date: str
    frequency: str
    market_scope: Sequence[str] = field(default_factory=lambda: ("cn", "hk"))
    universe: str = "mainstream"
    macro_assessment: Optional[MacroAssessment] = None
    sector_allocations: Sequence[SectorAllocation] = field(default_factory=tuple)
    position_guidance: Optional[PositionGuidance] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """Base class for all strategy plugins."""

    def __init__(self, config: StrategyConfig) -> None:
        config.validate()
        self.config = config

    @property
    def strategy_id(self) -> str:
        return self.config.strategy_id

    @property
    def required_factors(self) -> List[str]:
        return list(self.config.factors)

    @abstractmethod
    def generate_signals(self, factor_data: Any, context: StrategyContext) -> List[StrategySignal]:
        """Generate normalized strategy signals from prepared factor data."""

    def validate_context(self, context: StrategyContext) -> None:
        if context.frequency != self.config.frequency:
            raise ValueError(
                f"Strategy {self.strategy_id} expects frequency {self.config.frequency}, "
                f"got {context.frequency}"
            )
        unsupported = set(context.market_scope) - set(self.config.markets)
        if unsupported:
            raise ValueError(
                f"Strategy {self.strategy_id} does not support markets: {sorted(unsupported)}"
            )

    def should_run_stock_selection(self, context: StrategyContext) -> bool:
        if context.macro_assessment is None:
            return True
        return context.macro_assessment.allow_stock_selection

    def validate_signals(self, signals: Iterable[StrategySignal]) -> None:
        for signal in signals:
            if signal.strategy_id != self.strategy_id:
                raise ValueError(
                    f"Signal strategy_id {signal.strategy_id} does not match {self.strategy_id}"
                )
            signal.validate()
