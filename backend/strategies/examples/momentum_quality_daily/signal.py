from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from backend.strategies.base import BaseStrategy, StrategyContext
from backend.strategies.explanations import ExplanationContext, get_explanation_template
from backend.strategies.signals import (
    FactorContribution,
    StrategySignal,
    clamp_score,
    risk_level_from_score,
)


FACTOR_LABELS = {
    "momentum_20d": "20日趋势",
    "momentum_60d": "60日趋势",
    "quality_score": "质量评分",
    "amount_change_20d": "20日量能变化",
    "volatility_20d": "20日波动风险",
}


SCORE_WEIGHTS = {
    "momentum_20d": 0.35,
    "momentum_60d": 0.20,
    "quality_score": 0.25,
    "amount_change_20d": 0.10,
    "volatility_20d": -0.10,
}


@dataclass
class SecurityFactorRow:
    trade_date: str
    symbol: str
    market: str
    factor_scores: Dict[str, float] = field(default_factory=dict)
    factor_values: Dict[str, float] = field(default_factory=dict)


class MomentumQualityDailyStrategy(BaseStrategy):
    def generate_signals(self, factor_data: Any, context: StrategyContext) -> List[StrategySignal]:
        self.validate_context(context)
        rows = [
            row
            for row in normalize_factor_input(factor_data, context.trade_date)
            if row.market in context.market_scope and row.market in self.config.markets
        ]

        draft_signals = [self._build_signal(row, rank=1) for row in rows]

        signals: List[StrategySignal] = []
        for market in sorted({signal.market for signal in draft_signals}):
            market_signals = sorted(
                [signal for signal in draft_signals if signal.market == market],
                key=lambda item: item.score,
                reverse=True,
            )
            for rank, signal in enumerate(market_signals, start=1):
                signals.append(
                    StrategySignal(
                        trade_date=signal.trade_date,
                        strategy_id=signal.strategy_id,
                        symbol=signal.symbol,
                        market=signal.market,
                        score=signal.score,
                        rank=rank,
                        risk_score=signal.risk_score,
                        risk_level=signal.risk_level,
                        horizon=signal.horizon,
                        reason_summary=signal.reason_summary,
                        positive_factors=signal.positive_factors,
                        negative_factors=signal.negative_factors,
                        extra=signal.extra,
                    )
                )

        self.validate_signals(signals)
        return signals

    def _build_signal(self, row: SecurityFactorRow, rank: int) -> StrategySignal:
        scores = {
            name: clamp_score(row.factor_scores.get(name, 50.0))
            for name in self.required_factors
        }
        raw_score = (
            scores["momentum_20d"] * SCORE_WEIGHTS["momentum_20d"]
            + scores["momentum_60d"] * SCORE_WEIGHTS["momentum_60d"]
            + scores["quality_score"] * SCORE_WEIGHTS["quality_score"]
            + scores["amount_change_20d"] * SCORE_WEIGHTS["amount_change_20d"]
            + (100.0 - scores["volatility_20d"]) * abs(SCORE_WEIGHTS["volatility_20d"])
        )
        score = round(clamp_score(raw_score), 2)
        risk_score = round(
            clamp_score(scores["volatility_20d"] * 0.70 + (100.0 - scores["quality_score"]) * 0.30),
            2,
        )

        positive = [
            self._contribution("momentum_20d", row, "positive", "近20日趋势表现较好"),
            self._contribution("momentum_60d", row, "positive", "中期趋势有延续迹象"),
            self._contribution("quality_score", row, "positive", "质量因子对综合评分有支撑"),
            self._contribution("amount_change_20d", row, "positive", "近期成交活跃度改善"),
        ]
        negative = [
            self._contribution("volatility_20d", row, "negative", "波动越高，观察风险越高")
        ]

        explanation_template = get_explanation_template(self.config.explanation_template)
        explanation_context = ExplanationContext(
            trade_date=row.trade_date,
            strategy_id=self.strategy_id,
            symbol=row.symbol,
            market=row.market,
            scores=scores,
            risk_score=risk_score,
            positive_factors=positive,
            negative_factors=negative,
        )
        reason = explanation_template.render_reason_summary(explanation_context)
        return StrategySignal(
            trade_date=row.trade_date,
            strategy_id=self.strategy_id,
            symbol=row.symbol,
            market=row.market,
            score=score,
            rank=rank,
            risk_score=risk_score,
            risk_level=risk_level_from_score(risk_score),
            horizon=self.config.primary_horizon(),
            reason_summary=reason,
            positive_factors=positive,
            negative_factors=negative,
            extra={
                "model_type": self.config.model.get("type", "rule"),
                "explanation_template": self.config.explanation_template,
                "risk_note": explanation_template.render_risk_note(explanation_context),
            },
        )

    def _contribution(
        self,
        factor_name: str,
        row: SecurityFactorRow,
        direction: str,
        explanation: str,
    ) -> FactorContribution:
        score = clamp_score(row.factor_scores.get(factor_name, 50.0))
        weight = SCORE_WEIGHTS.get(factor_name, 0.0)
        return FactorContribution(
            factor_name=factor_name,
            display_name=FACTOR_LABELS.get(factor_name, factor_name),
            value=float(row.factor_values.get(factor_name, score)),
            score=round(score, 2),
            weight=weight,
            direction=direction,
            explanation=explanation,
        )


def normalize_factor_input(factor_data: Any, default_trade_date: str) -> List[SecurityFactorRow]:
    records = to_records(factor_data)
    grouped: Dict[Tuple[str, str, str], SecurityFactorRow] = {}

    for record in records:
        trade_date = str(record.get("trade_date") or default_trade_date)
        symbol = str(record.get("symbol", "")).strip()
        market = str(record.get("market", "")).strip()
        if not symbol or not market:
            continue

        key = (trade_date, symbol, market)
        row = grouped.setdefault(
            key,
            SecurityFactorRow(trade_date=trade_date, symbol=symbol, market=market),
        )

        if "factor_name" in record:
            factor_name = str(record["factor_name"])
            row.factor_scores[factor_name] = float(record.get("factor_score", 50.0))
            row.factor_values[factor_name] = float(
                record.get("factor_value", row.factor_scores[factor_name])
            )
        else:
            for factor_name in FACTOR_LABELS:
                if factor_name in record:
                    value = float(record[factor_name])
                    row.factor_scores[factor_name] = value
                    row.factor_values[factor_name] = value

    return list(grouped.values())


def to_records(factor_data: Any) -> List[Mapping[str, Any]]:
    if factor_data is None:
        return []
    if hasattr(factor_data, "to_dict"):
        try:
            return list(factor_data.to_dict(orient="records"))
        except TypeError:
            pass
    if isinstance(factor_data, Mapping):
        rows = factor_data.get("rows")
        if rows is not None:
            return list(rows)
        return [factor_data]
    if isinstance(factor_data, Iterable) and not isinstance(factor_data, (str, bytes)):
        return list(factor_data)
    raise TypeError("factor_data must be a mapping, iterable of mappings, or dataframe-like object")
