from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence

from .signals import FactorContribution


@dataclass(frozen=True)
class ExplanationContext:
    trade_date: str
    strategy_id: str
    symbol: str
    market: str
    scores: Mapping[str, float]
    risk_score: float
    positive_factors: Sequence[FactorContribution] = field(default_factory=tuple)
    negative_factors: Sequence[FactorContribution] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseExplanationTemplate(ABC):
    template_id: str = ""

    @abstractmethod
    def render_reason_summary(self, context: ExplanationContext) -> str:
        """Render the beginner-facing selection reason."""

    def render_risk_note(self, context: ExplanationContext) -> str:
        if context.risk_score < 30:
            return "风险评分较低，仍需结合市场环境持续观察。"
        if context.risk_score < 55:
            return "风险评分处于中等水平，适合作为观察候选。"
        if context.risk_score < 75:
            return "风险评分偏高，应重点关注波动和回撤。"
        return "风险评分较高，不适合只看综合分数做判断。"


class DefaultStockSelectionTemplate(BaseExplanationTemplate):
    template_id = "default_stock_selection"

    def render_reason_summary(self, context: ExplanationContext) -> str:
        scores = context.scores
        strengths = []
        if scores.get("momentum_20d", 50.0) >= 70:
            strengths.append("短期趋势较强")
        if scores.get("momentum_60d", 50.0) >= 70:
            strengths.append("中期趋势较稳")
        if scores.get("quality_score", 50.0) >= 70:
            strengths.append("质量评分较好")
        if scores.get("amount_change_20d", 50.0) >= 65:
            strengths.append("成交活跃度提升")

        if not strengths:
            strengths.append("综合因子表现相对均衡")

        risk_text = "波动风险可控" if context.risk_score < 55 else "波动偏高，需要控制观察仓位"
        return "，".join(strengths) + f"；{risk_text}。"


class ExplanationTemplateRegistry:
    def __init__(self) -> None:
        self._templates: Dict[str, BaseExplanationTemplate] = {}

    def register(self, template: BaseExplanationTemplate) -> None:
        if not template.template_id:
            raise ValueError("template_id is required")
        if template.template_id in self._templates:
            raise ValueError(f"Explanation template already registered: {template.template_id}")
        self._templates[template.template_id] = template

    def get(self, template_id: str) -> BaseExplanationTemplate:
        if template_id not in self._templates:
            raise KeyError(f"Unknown explanation_template: {template_id}")
        return self._templates[template_id]

    def list_template_ids(self) -> list[str]:
        return sorted(self._templates)


def build_default_explanation_registry() -> ExplanationTemplateRegistry:
    registry = ExplanationTemplateRegistry()
    registry.register(DefaultStockSelectionTemplate())
    return registry


DEFAULT_EXPLANATION_REGISTRY = build_default_explanation_registry()


def get_explanation_template(template_id: str) -> BaseExplanationTemplate:
    return DEFAULT_EXPLANATION_REGISTRY.get(template_id)
