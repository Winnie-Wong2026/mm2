from copy import deepcopy
from typing import Optional

from backend.api.watchlist_store import watchlist_store


MOCK_UPDATED_AT = "2026-05-22T18:30:00+08:00"
MOCK_PUBLISHED_AT = "2026-05-22T19:00:00+08:00"
DEFAULT_STRATEGY_ID = "momentum_quality_daily"
RISK_NOTICE = "本报告仅用于内部研究参考，不构成投资建议。"

_MACRO_REGIME = {
    "as_of": "2026-05-22T17:40:00+08:00",
    "status": "允许轻仓观察",
    "allow_stock_selection": True,
    "regime": "结构性中性偏谨慎",
    "confidence": 72,
    "summary": "宏观环境没有触发全面回避，但波动中等偏高，应先控制总仓位。",
    "macro_signals": [
        {"label": "流动性", "value": "中性", "tone": "资金面未明显收紧"},
        {"label": "风险偏好", "value": "谨慎", "tone": "高波动主题需要降权"},
        {"label": "跨市场", "value": "分化", "tone": "A股偏结构，港股修复但扰动更高"},
    ],
    "sector_allocation": [
        {"name": "高端制造", "stance": "优先观察", "target": "25%", "reason": "趋势改善"},
        {"name": "互联网平台", "stance": "谨慎增配", "target": "20%", "reason": "修复延续"},
        {"name": "金融", "stance": "防守配置", "target": "20%", "reason": "波动较低"},
        {"name": "半导体", "stance": "控制仓位", "target": "15%", "reason": "热度和波动同步高"},
    ],
    "position_guidance": {
        "gross": "30% 到 50%",
        "single_stock": "单只不超过 8%",
        "cash_buffer": "保留至少 50% 现金或低风险仓位",
        "rebalance": "宏观状态维持允许观察时，再按日频榜单小步调整。",
    },
    "risk_reminders": [
        "若市场波动继续上升，先降总仓位，再减少高波动行业暴露。",
        "行业方向不清晰时，只保留观察名单，不扩大候选股数量。",
        "任何个股入选都不能覆盖宏观风险和组合仓位约束。",
    ],
}

_STRATEGIES = [
    {
        "strategy_id": "momentum_quality_daily",
        "name": "均衡质量精选",
        "description": "在趋势、质量、估值和波动之间保持均衡，适合作为默认观察池。",
        "model_type": "rule",
        "frequency": "daily",
        "markets": ["cn", "hk"],
        "enabled": True,
        "is_default": True,
    },
    {
        "strategy_id": "defensive_value_daily",
        "name": "稳健低波策略",
        "description": "优先选择质量稳定、波动较低、估值不过度透支的候选股。",
        "model_type": "rule",
        "frequency": "daily",
        "markets": ["cn", "hk"],
        "enabled": True,
        "is_default": False,
    },
    {
        "strategy_id": "active_growth_daily",
        "name": "成长动量增强",
        "description": "更重视趋势动量和成交活跃度，适合寻找短中期弹性更强的候选股。",
        "model_type": "rule",
        "frequency": "daily",
        "markets": ["cn", "hk"],
        "enabled": True,
        "is_default": False,
    },
    {
        "strategy_id": "hk_recovery_daily",
        "name": "港股修复优先",
        "description": "优先观察港股互联网、金融和高弹性修复方向，同时保留 A股候选作对照。",
        "model_type": "rule",
        "frequency": "daily",
        "markets": ["cn", "hk"],
        "enabled": True,
        "is_default": False,
    },
]


_RANKINGS = [
    {
        "symbol": "600519.SH",
        "name": "贵州茅台",
        "market": "cn",
        "exchange": "sse",
        "industry": "食品饮料",
        "rank": 1,
        "score": 92.5,
        "risk_level": "中",
        "horizon": "20日",
        "reason_summary": "趋势稳定，成交活跃，盈利质量较好。",
        "positive_factors": ["20日趋势较强", "成交额稳定", "ROE 较高"],
        "negative_factors": ["估值不低", "短期波动上升"],
        "frequency": "daily",
        "strategy_id": DEFAULT_STRATEGY_ID,
        "updated_at": MOCK_UPDATED_AT,
    },
    {
        "symbol": "300750.SZ",
        "name": "宁德时代",
        "market": "cn",
        "exchange": "szse",
        "industry": "电力设备",
        "rank": 2,
        "score": 89.3,
        "risk_level": "中高",
        "horizon": "10日",
        "reason_summary": "行业热度较高，成交活跃，但短期波动也偏大。",
        "positive_factors": ["资金活跃度提升", "行业景气度较高", "20日动量改善"],
        "negative_factors": ["波动偏高", "对市场情绪较敏感"],
        "frequency": "daily",
        "strategy_id": DEFAULT_STRATEGY_ID,
        "updated_at": MOCK_UPDATED_AT,
    },
    {
        "symbol": "00700.HK",
        "name": "腾讯控股",
        "market": "hk",
        "exchange": "hkex",
        "industry": "互联网",
        "rank": 1,
        "score": 91.1,
        "risk_level": "中",
        "horizon": "20日",
        "reason_summary": "趋势和质量因子表现较均衡，流动性充足。",
        "positive_factors": ["成交额充足", "盈利质量较稳", "趋势修复"],
        "negative_factors": ["受外部市场情绪影响", "政策预期仍需观察"],
        "frequency": "daily",
        "strategy_id": DEFAULT_STRATEGY_ID,
        "updated_at": MOCK_UPDATED_AT,
    },
    {
        "symbol": "03690.HK",
        "name": "美团-W",
        "market": "hk",
        "exchange": "hkex",
        "industry": "互联网服务",
        "rank": 2,
        "score": 86.7,
        "risk_level": "中高",
        "horizon": "10日",
        "reason_summary": "短期资金关注度提升，但波动和回撤风险较高。",
        "positive_factors": ["成交活跃", "短期反弹动能增强"],
        "negative_factors": ["波动偏高", "盈利预期分歧较大"],
        "frequency": "daily",
        "strategy_id": DEFAULT_STRATEGY_ID,
        "updated_at": MOCK_UPDATED_AT,
    },
    {
        "symbol": "000333.SZ",
        "name": "美的集团",
        "market": "cn",
        "exchange": "szse",
        "industry": "家用电器",
        "rank": 1,
        "score": 88.6,
        "risk_level": "中",
        "horizon": "4周",
        "reason_summary": "盈利质量和估值匹配度较好，适合中短期持续观察。",
        "positive_factors": ["估值较稳", "ROE 表现较好", "回撤控制较好"],
        "negative_factors": ["行业弹性一般"],
        "frequency": "weekly",
        "strategy_id": DEFAULT_STRATEGY_ID,
        "updated_at": MOCK_UPDATED_AT,
    },
    {
        "symbol": "00941.HK",
        "name": "中国移动",
        "market": "hk",
        "exchange": "hkex",
        "industry": "电信服务",
        "rank": 1,
        "score": 87.9,
        "risk_level": "低",
        "horizon": "4周",
        "reason_summary": "波动较低，现金流和股息属性较稳定。",
        "positive_factors": ["低波动", "成交稳定", "防御属性较强"],
        "negative_factors": ["短期弹性有限"],
        "frequency": "weekly",
        "strategy_id": DEFAULT_STRATEGY_ID,
        "updated_at": MOCK_UPDATED_AT,
    },
]

_STRATEGY_VARIANT_OVERRIDES = {
    "defensive_value_daily": {
        "600519.SH": {
            "rank": 1,
            "score": 90.4,
            "reason_summary": "质量和低波动表现更稳，适合稳健低波策略观察。",
        },
        "300750.SZ": {
            "rank": 2,
            "score": 80.2,
            "reason_summary": "成长弹性较高，但波动对稳健低波策略扣分明显。",
        },
        "00700.HK": {
            "rank": 1,
            "score": 88.8,
            "reason_summary": "质量、流动性和波动控制较均衡，适合港股稳健观察。",
        },
        "03690.HK": {
            "rank": 2,
            "score": 78.5,
            "reason_summary": "短期修复明显，但波动和盈利预期分歧压低稳健评分。",
        },
        "000333.SZ": {
            "rank": 1,
            "score": 91.2,
            "reason_summary": "估值、质量和回撤控制较好，稳健低波周频排序靠前。",
        },
        "00941.HK": {
            "rank": 1,
            "score": 90.6,
            "reason_summary": "低波动和现金流属性突出，适合港股稳健样例。",
        },
    },
    "active_growth_daily": {
        "600519.SH": {
            "rank": 2,
            "score": 82.6,
            "reason_summary": "质量稳定，但成长动量策略更偏好高成交弹性。",
        },
        "300750.SZ": {
            "rank": 1,
            "score": 91.5,
            "reason_summary": "趋势和成交活跃度改善明显，成长动量评分领先。",
        },
        "00700.HK": {
            "rank": 2,
            "score": 84.3,
            "reason_summary": "综合均衡，但活跃弹性略弱于高波动修复样本。",
        },
        "03690.HK": {
            "rank": 1,
            "score": 89.8,
            "reason_summary": "短期修复和成交活跃度更突出，成长动量策略排序靠前。",
        },
        "000333.SZ": {
            "rank": 1,
            "score": 82.4,
            "reason_summary": "周频质量较稳，但成长动量弹性一般。",
        },
        "00941.HK": {
            "rank": 1,
            "score": 79.8,
            "reason_summary": "防御属性强，但成长动量策略下弹性较有限。",
        },
    },
    "hk_recovery_daily": {
        "600519.SH": {
            "rank": 1,
            "score": 83.5,
            "reason_summary": "作为 A股对照样本，质量稳定但不是港股修复主线。",
        },
        "300750.SZ": {
            "rank": 2,
            "score": 81.4,
            "reason_summary": "作为高弹性 A股对照样本，波动仍需重点跟踪。",
        },
        "00700.HK": {
            "rank": 1,
            "score": 92.2,
            "reason_summary": "港股核心资产修复延续，流动性和趋势均衡。",
        },
        "03690.HK": {
            "rank": 2,
            "score": 88.6,
            "reason_summary": "港股修复弹性突出，但短期波动也较高。",
        },
        "000333.SZ": {
            "rank": 1,
            "score": 80.1,
            "reason_summary": "周频稳健，但在港股修复策略中主要作为 A股对照。",
        },
        "00941.HK": {
            "rank": 1,
            "score": 88.4,
            "reason_summary": "港股低波动修复样本，适合作为防御侧对照。",
        },
    },
}

for strategy_id, overrides in _STRATEGY_VARIANT_OVERRIDES.items():
    for source in list(_RANKINGS):
        override = overrides.get(source["symbol"])
        if not override:
            continue
        variant = deepcopy(source)
        variant.update(override)
        variant["strategy_id"] = strategy_id
        _RANKINGS.append(variant)

_STOCK_DETAILS = {
    "600519.SH": {
        "symbol": "600519.SH",
        "name": "贵州茅台",
        "market": "cn",
        "exchange": "sse",
        "industry": "食品饮料",
        "score": 92.5,
        "rank": 1,
        "risk_level": "中",
        "horizon": "20日",
        "reason_summary": "趋势稳定，成交活跃，盈利质量较好。",
        "advantages": ["盈利质量稳", "行业地位强", "成交额保持在较高水平"],
        "risks": ["估值不低", "短期波动上升"],
        "recent_performance": {
            "return_5d": 2.1,
            "return_20d": 6.4,
            "max_drawdown_20d": -4.8,
        },
        "factor_summary": [
            {
                "factor_name": "momentum_20d",
                "factor_label": "20日趋势",
                "score": 88.0,
                "explanation": "最近 20 日相对市场走势较强。",
            },
            {
                "factor_name": "quality_roe",
                "factor_label": "盈利质量",
                "score": 93.0,
                "explanation": "盈利质量因子在同市场样本中排名靠前。",
            },
        ],
        "price_series": [
            {"trade_date": "2026-05-20", "close": 1652.0, "amount": 4680000000},
            {"trade_date": "2026-05-21", "close": 1671.5, "amount": 4950000000},
            {"trade_date": "2026-05-22", "close": 1688.0, "amount": 5200000000},
        ],
        "updated_at": MOCK_UPDATED_AT,
    },
    "300750.SZ": {
        "symbol": "300750.SZ",
        "name": "宁德时代",
        "market": "cn",
        "exchange": "szse",
        "industry": "电力设备",
        "score": 89.3,
        "rank": 2,
        "risk_level": "中高",
        "horizon": "10日",
        "reason_summary": "行业热度较高，成交活跃，但短期波动也偏大。",
        "advantages": ["资金关注度提升", "行业景气度较高"],
        "risks": ["短期波动偏大", "对市场情绪较敏感"],
        "recent_performance": {
            "return_5d": 4.6,
            "return_20d": 8.9,
            "max_drawdown_20d": -9.7,
        },
        "factor_summary": [
            {
                "factor_name": "liquidity_amount_20d",
                "factor_label": "成交活跃度",
                "score": 91.0,
                "explanation": "20 日成交额处在较高水平。",
            }
        ],
        "price_series": [
            {"trade_date": "2026-05-20", "close": 205.2, "amount": 7200000000},
            {"trade_date": "2026-05-21", "close": 209.8, "amount": 7600000000},
            {"trade_date": "2026-05-22", "close": 213.4, "amount": 8300000000},
        ],
        "updated_at": MOCK_UPDATED_AT,
    },
    "00700.HK": {
        "symbol": "00700.HK",
        "name": "腾讯控股",
        "market": "hk",
        "exchange": "hkex",
        "industry": "互联网",
        "score": 91.1,
        "rank": 1,
        "risk_level": "中",
        "horizon": "20日",
        "reason_summary": "趋势和质量因子表现较均衡，流动性充足。",
        "advantages": ["流动性充足", "盈利质量较稳", "趋势修复"],
        "risks": ["受外部市场情绪影响", "政策预期仍需观察"],
        "recent_performance": {
            "return_5d": 3.4,
            "return_20d": 7.2,
            "max_drawdown_20d": -6.1,
        },
        "factor_summary": [
            {
                "factor_name": "momentum_20d",
                "factor_label": "20日趋势",
                "score": 86.0,
                "explanation": "趋势修复，且成交额支持较好。",
            }
        ],
        "price_series": [
            {"trade_date": "2026-05-20", "close": 383.2, "amount": 8100000000},
            {"trade_date": "2026-05-21", "close": 388.6, "amount": 8450000000},
            {"trade_date": "2026-05-22", "close": 392.0, "amount": 9000000000},
        ],
        "updated_at": MOCK_UPDATED_AT,
    },
    "03690.HK": {
        "symbol": "03690.HK",
        "name": "美团-W",
        "market": "hk",
        "exchange": "hkex",
        "industry": "互联网服务",
        "score": 86.7,
        "rank": 2,
        "risk_level": "中高",
        "horizon": "10日",
        "reason_summary": "短期资金关注度提升，但波动和回撤风险较高。",
        "advantages": ["成交活跃", "短期反弹动能增强"],
        "risks": ["波动偏高", "盈利预期分歧较大"],
        "recent_performance": {
            "return_5d": 5.8,
            "return_20d": 9.5,
            "max_drawdown_20d": -12.2,
        },
        "factor_summary": [
            {
                "factor_name": "short_term_reversal",
                "factor_label": "短期反弹",
                "score": 84.0,
                "explanation": "短期修复力度较强，但波动也明显放大。",
            }
        ],
        "price_series": [
            {"trade_date": "2026-05-20", "close": 116.2, "amount": 5300000000},
            {"trade_date": "2026-05-21", "close": 119.4, "amount": 5900000000},
            {"trade_date": "2026-05-22", "close": 121.8, "amount": 6200000000},
        ],
        "updated_at": MOCK_UPDATED_AT,
    },
    "000333.SZ": {
        "symbol": "000333.SZ",
        "name": "美的集团",
        "market": "cn",
        "exchange": "szse",
        "industry": "家用电器",
        "score": 88.6,
        "rank": 1,
        "risk_level": "中",
        "horizon": "4周",
        "reason_summary": "盈利质量和估值匹配度较好，适合中短期持续观察。",
        "advantages": ["盈利质量较稳", "估值匹配度较好"],
        "risks": ["行业弹性一般"],
        "recent_performance": {
            "return_5d": 1.3,
            "return_20d": 4.1,
            "max_drawdown_20d": -3.5,
        },
        "factor_summary": [
            {
                "factor_name": "value_quality",
                "factor_label": "估值质量",
                "score": 87.0,
                "explanation": "估值和盈利质量组合表现较均衡。",
            }
        ],
        "price_series": [
            {"trade_date": "2026-05-20", "close": 70.2, "amount": 2100000000},
            {"trade_date": "2026-05-21", "close": 71.1, "amount": 2300000000},
            {"trade_date": "2026-05-22", "close": 71.5, "amount": 2400000000},
        ],
        "updated_at": MOCK_UPDATED_AT,
    },
    "00941.HK": {
        "symbol": "00941.HK",
        "name": "中国移动",
        "market": "hk",
        "exchange": "hkex",
        "industry": "电信服务",
        "score": 87.9,
        "rank": 1,
        "risk_level": "低",
        "horizon": "4周",
        "reason_summary": "波动较低，现金流和股息属性较稳定。",
        "advantages": ["低波动", "现金流稳定", "防御属性较强"],
        "risks": ["短期弹性有限"],
        "recent_performance": {
            "return_5d": 1.0,
            "return_20d": 3.2,
            "max_drawdown_20d": -2.1,
        },
        "factor_summary": [
            {
                "factor_name": "low_volatility",
                "factor_label": "低波动",
                "score": 90.0,
                "explanation": "近期价格波动低于多数港股样本。",
            }
        ],
        "price_series": [
            {"trade_date": "2026-05-20", "close": 78.4, "amount": 1550000000},
            {"trade_date": "2026-05-21", "close": 78.9, "amount": 1640000000},
            {"trade_date": "2026-05-22", "close": 79.1, "amount": 1700000000},
        ],
        "updated_at": MOCK_UPDATED_AT,
    },
}

_REPORTS = [
    {
        "report_id": "daily-2026-05-22",
        "title": "2026-05-22 AI 候选股日报",
        "frequency": "daily",
        "markets": ["cn", "hk"],
        "summary": "A股和港股候选股整体偏向趋势和质量因子。",
        "published_at": MOCK_PUBLISHED_AT,
        "sections": [
            {
                "heading": "市场概览",
                "content": "今日市场分化，资金更偏好高流动性和盈利质量较稳的公司。",
            },
            {
                "heading": "A股候选股",
                "content": "贵州茅台、宁德时代进入 mock 日频榜单，分别代表质量稳定和景气成长方向。",
            },
            {
                "heading": "港股候选股",
                "content": "腾讯控股和美团-W 进入 mock 日频榜单，但互联网板块仍需关注波动风险。",
            },
        ],
        "risk_notice": RISK_NOTICE,
    },
    {
        "report_id": "weekly-2026-W21",
        "title": "2026年第21周 AI 候选股周报",
        "frequency": "weekly",
        "markets": ["cn", "hk"],
        "summary": "本周 mock 周频榜单偏向低波动、质量和防御属性。",
        "published_at": MOCK_PUBLISHED_AT,
        "sections": [
            {
                "heading": "本周风格",
                "content": "周频候选股更强调回撤控制、估值稳定和成交额连续性。",
            },
            {
                "heading": "观察重点",
                "content": "美的集团和中国移动进入周频 mock 榜单，可用于前端报告中心联调。",
            },
        ],
        "risk_notice": RISK_NOTICE,
    },
]

def paginate(items: list, page: int, page_size: int) -> tuple[list, int]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total


def get_macro_regime() -> dict:
    return deepcopy(_MACRO_REGIME)


def list_strategies() -> list:
    return deepcopy(_STRATEGIES)


def list_rankings(
    market: str,
    frequency: str,
    top_n: int,
    strategy_id: str,
    page: int,
    page_size: int,
) -> tuple[list, int]:
    filtered = [
        item
        for item in _RANKINGS
        if item["market"] == market
        and item["frequency"] == frequency
        and item["strategy_id"] == strategy_id
        and item["rank"] <= top_n
    ]
    filtered.sort(key=lambda item: item["rank"])
    clean_items = [
        {key: value for key, value in item.items() if key not in {"frequency", "strategy_id"}}
        for item in filtered
    ]
    page_items, total = paginate(clean_items, page, page_size)
    return deepcopy(page_items), total


def get_stock_detail(symbol: str) -> Optional[dict]:
    return deepcopy(_STOCK_DETAILS.get(symbol.upper()))


def list_watchlist(
    username: str,
    market: Optional[str],
    risk_level: Optional[str],
    page: int,
    page_size: int,
) -> tuple[list, int]:
    entries = watchlist_store.list_entries(username)
    items = []
    for entry in entries:
        detail = _STOCK_DETAILS.get(entry["symbol"])
        if not detail:
            continue
        item = {
            "symbol": detail["symbol"],
            "name": detail["name"],
            "market": detail["market"],
            "risk_level": detail["risk_level"],
            "latest_rank": detail["rank"],
            "latest_score": detail["score"],
            "still_on_ranking": any(row["symbol"] == detail["symbol"] for row in _RANKINGS),
            "note": entry.get("note"),
            "created_at": entry["created_at"],
        }
        if market and item["market"] != market:
            continue
        if risk_level and item["risk_level"] != risk_level:
            continue
        items.append(item)
    page_items, total = paginate(items, page, page_size)
    return deepcopy(page_items), total


def add_watchlist_item(username: str, symbol: str, note: Optional[str]) -> tuple[Optional[dict], Optional[str]]:
    normalized_symbol = symbol.upper()
    detail = _STOCK_DETAILS.get(normalized_symbol)
    if not detail:
        return None, "not_found"

    entries = watchlist_store.list_entries(username)
    if any(entry["symbol"] == normalized_symbol for entry in entries):
        return None, "exists"

    created_at = watchlist_store.add_entry(username, normalized_symbol, note)
    if created_at is None:
        return None, "exists"
    item = {
        "symbol": detail["symbol"],
        "name": detail["name"],
        "market": detail["market"],
        "risk_level": detail["risk_level"],
        "latest_rank": detail["rank"],
        "latest_score": detail["score"],
        "still_on_ranking": any(row["symbol"] == detail["symbol"] for row in _RANKINGS),
        "note": note,
        "created_at": created_at,
    }
    return deepcopy(item), None


def remove_watchlist_item(username: str, symbol: str) -> bool:
    return watchlist_store.remove_entry(username, symbol)


def list_reports(
    frequency: Optional[str],
    market: Optional[str],
    page: int,
    page_size: int,
) -> tuple[list, int]:
    reports = []
    for report in _REPORTS:
        if frequency and report["frequency"] != frequency:
            continue
        if market and market not in report["markets"]:
            continue
        reports.append(
            {
                "report_id": report["report_id"],
                "title": report["title"],
                "frequency": report["frequency"],
                "markets": report["markets"],
                "summary": report["summary"],
                "published_at": report["published_at"],
            }
        )
    page_items, total = paginate(reports, page, page_size)
    return deepcopy(page_items), total


def get_report_detail(report_id: str) -> Optional[dict]:
    for report in _REPORTS:
        if report["report_id"] == report_id:
            return deepcopy(report)
    return None
