"""Strategy plugin framework."""

from .base import BaseStrategy, MacroAssessment, PositionGuidance, SectorAllocation, StrategyContext
from .config import StrategyConfig
from .explanations import (
    BaseExplanationTemplate,
    DefaultStockSelectionTemplate,
    ExplanationContext,
    ExplanationTemplateRegistry,
)
from .registry import StrategyRegistry
from .signals import FactorContribution, StrategySignal

__all__ = [
    "BaseExplanationTemplate",
    "BaseStrategy",
    "DefaultStockSelectionTemplate",
    "ExplanationContext",
    "ExplanationTemplateRegistry",
    "FactorContribution",
    "MacroAssessment",
    "PositionGuidance",
    "SectorAllocation",
    "StrategyConfig",
    "StrategyContext",
    "StrategyRegistry",
    "StrategySignal",
]
