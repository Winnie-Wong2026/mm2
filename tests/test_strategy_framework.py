from backend.scoring import SimpleTopNScoringEngine
from backend.strategies import StrategyContext
from backend.strategies.explanations import DEFAULT_EXPLANATION_REGISTRY
from backend.strategies.registry import build_registry


def test_registry_discovers_example_strategy() -> None:
    registry = build_registry()

    assert registry.list_strategy_ids() == ["momentum_quality_daily"]
    config = registry.get_config("momentum_quality_daily")
    assert config.explanation_template == "default_stock_selection"
    assert config.markets == ["cn", "hk"]


def test_example_strategy_generates_ranked_signals_and_rankings() -> None:
    registry = build_registry()
    strategy = registry.create("momentum_quality_daily")
    context = StrategyContext(trade_date="2026-05-22", frequency="daily", market_scope=("cn", "hk"))
    factor_rows = [
        {
            "trade_date": "2026-05-22",
            "symbol": "600519.SH",
            "market": "cn",
            "momentum_20d": 88,
            "momentum_60d": 82,
            "quality_score": 91,
            "amount_change_20d": 70,
            "volatility_20d": 35,
        },
        {
            "trade_date": "2026-05-22",
            "symbol": "300750.SZ",
            "market": "cn",
            "momentum_20d": 72,
            "momentum_60d": 68,
            "quality_score": 65,
            "amount_change_20d": 78,
            "volatility_20d": 62,
        },
        {
            "trade_date": "2026-05-22",
            "symbol": "00700.HK",
            "market": "hk",
            "momentum_20d": 85,
            "momentum_60d": 76,
            "quality_score": 80,
            "amount_change_20d": 68,
            "volatility_20d": 42,
        },
    ]

    signals = strategy.generate_signals(factor_rows, context)

    cn_symbols = [signal.symbol for signal in signals if signal.market == "cn"]
    assert cn_symbols == ["600519.SH", "300750.SZ"]
    assert [signal.rank for signal in signals if signal.market == "cn"] == [1, 2]
    assert signals[0].reason_summary
    assert signals[0].extra["explanation_template"] == "default_stock_selection"
    assert signals[0].extra["risk_note"]

    rankings = SimpleTopNScoringEngine().build_rankings(signals, context.frequency, [1])

    assert len(rankings) == 2
    assert {ranking.market for ranking in rankings} == {"cn", "hk"}
    assert all(ranking.top_n == 1 for ranking in rankings)
    assert all(len(ranking.candidates) == 1 for ranking in rankings)


def test_default_explanation_template_is_registered() -> None:
    assert DEFAULT_EXPLANATION_REGISTRY.list_template_ids() == ["default_stock_selection"]
