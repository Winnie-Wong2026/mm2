from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class FactorContext:
    trade_date: str
    frequency: str = "daily"
    universe: str = "mainstream"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FactorValue:
    trade_date: str
    symbol: str
    market: str
    factor_name: str
    factor_value: float
    factor_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseFactor(ABC):
    factor_name: str = ""
    display_name: str = ""
    dependencies: List[str] = []

    @abstractmethod
    def calculate(self, input_data: Any, context: FactorContext) -> List[FactorValue]:
        """Calculate factor values from prepared local data."""

