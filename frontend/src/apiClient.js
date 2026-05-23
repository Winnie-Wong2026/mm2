import {
  marketSummary as mockMarketSummary,
  macroRegime as mockMacroRegime,
  reports as mockReports,
  stocks as mockStocks,
  strategyProfiles as mockStrategyProfiles
} from "./mockData.js";

const API_BASE = localStorage.getItem("mm2-api-base") || "http://127.0.0.1:8000";
const TOKEN_KEY = "mm2-api-token";
const DEMO_USER = { username: "researcher", password: "research123" };

let accessToken = localStorage.getItem(TOKEN_KEY) || "";

function endpoint(path) {
  return `${API_BASE}${path}`;
}

async function login() {
  const response = await fetch(endpoint("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(DEMO_USER)
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.error?.message || "后端登录失败");
  }
  accessToken = payload.data.access_token;
  localStorage.setItem(TOKEN_KEY, accessToken);
  return accessToken;
}

async function apiRequest(path, options = {}, allowRetry = true) {
  if (!accessToken) {
    await login();
  }
  const response = await fetch(endpoint(path), {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
      Authorization: `Bearer ${accessToken}`
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401 && allowRetry) {
    localStorage.removeItem(TOKEN_KEY);
    accessToken = "";
    await login();
    return apiRequest(path, options, false);
  }
  if (!response.ok) {
    throw new Error(payload?.error?.message || `API 请求失败：${path}`);
  }
  return payload.data;
}

function formatDateTime(value) {
  if (!value) return mockMarketSummary.updatedAt;
  return value.replace("T", " ").replace("+08:00", "").slice(0, 16);
}

function transformMacroRegime(data) {
  if (!data) return mockMacroRegime;
  return {
    asOf: formatDateTime(data.as_of),
    status: data.status,
    allowStockSelection: data.allow_stock_selection,
    regime: data.regime,
    confidence: data.confidence,
    summary: data.summary,
    macroSignals: data.macro_signals || [],
    sectorAllocation: data.sector_allocation || [],
    positionGuidance: {
      gross: data.position_guidance?.gross || mockMacroRegime.positionGuidance.gross,
      singleStock: data.position_guidance?.single_stock || mockMacroRegime.positionGuidance.singleStock,
      cashBuffer: data.position_guidance?.cash_buffer || mockMacroRegime.positionGuidance.cashBuffer,
      rebalance: data.position_guidance?.rebalance || mockMacroRegime.positionGuidance.rebalance
    },
    riskReminders: data.risk_reminders || []
  };
}

function transformStrategies(items) {
  if (!items?.length) return mockStrategyProfiles;
  return items.map((item) => {
    const fallback = mockStrategyProfiles.find((strategy) => strategy.id === item.strategy_id)
      || mockStrategyProfiles[0];
    return {
      ...fallback,
      id: item.strategy_id,
      name: item.name,
      description: item.description,
      apiHint: `strategy_id=${item.strategy_id}`,
      universe: item.markets?.includes("hk") ? fallback.universe : "A股",
      horizon: item.frequency === "weekly" ? "4 到 12 周" : fallback.horizon
    };
  });
}

function rankingToStock(row, frequency) {
  const fallback = mockStocks.find((stock) => stock.id === row.symbol);
  const positive = row.positive_factors || fallback?.strengths || [];
  const negative = row.negative_factors || fallback?.risks || [];
  return {
    ...(fallback || {}),
    id: row.symbol,
    name: row.name || fallback?.name || row.symbol,
    symbol: row.symbol,
    market: row.market,
    board: row.market === "hk" ? "港股" : "A股",
    industry: row.industry || fallback?.industry || "待分类",
    score: Math.round(row.score || fallback?.score || 70),
    risk: row.risk_level || fallback?.risk || "中",
    horizon: row.horizon || fallback?.horizon || "20日",
    dailyRank: frequency === "daily" ? row.rank : fallback?.dailyRank || 99,
    weeklyRank: frequency === "weekly" ? row.rank : fallback?.weeklyRank || 99,
    change: fallback?.change || "待更新",
    consecutive: fallback?.consecutive || 1,
    summary: row.reason_summary || fallback?.summary || "后端 API 返回的候选股样本。",
    strengths: positive.length ? positive : ["综合评分较高"],
    risks: negative.length ? negative : ["需等待更多数据验证"],
    factors: fallback?.factors || {
      trend: 72,
      liquidity: 70,
      valuation: 60,
      quality: 68,
      volatility: 48
    },
    priceSeries: fallback?.priceSeries || [45, 47, 46, 49, 50, 52, 51, 54],
    explain: row.reason_summary || fallback?.explain || "来自后端 API 的候选解释。",
    apiHint: `/api/stocks/${row.symbol}`
  };
}

function mergeRankingStocks(rankingGroups) {
  const merged = new Map(mockStocks.map((stock) => [stock.id, { ...stock }]));
  for (const { frequency, rows } of rankingGroups) {
    for (const row of rows || []) {
      const stock = rankingToStock(row, frequency);
      const existing = merged.get(stock.id) || stock;
      merged.set(stock.id, {
        ...existing,
        ...stock,
        dailyRank: frequency === "daily" ? stock.dailyRank : existing.dailyRank,
        weeklyRank: frequency === "weekly" ? stock.weeklyRank : existing.weeklyRank
      });
    }
  }
  return [...merged.values()];
}

function transformReports(summaries, details) {
  const detailById = new Map((details || []).filter(Boolean).map((item) => [item.report_id, item]));
  const rows = summaries?.length ? summaries : [];
  if (!rows.length) return mockReports;
  return rows.map((item) => {
    const detail = detailById.get(item.report_id);
    return {
      id: item.report_id,
      title: item.title,
      type: item.frequency === "weekly" ? "周频" : "日频",
      date: formatDateTime(item.published_at).slice(0, 10),
      status: "已生成",
      summary: item.summary,
      sections: detail?.sections?.map((section) => `${section.heading}：${section.content}`)
        || ["报告详情等待后端返回"],
      apiHint: `/api/reports/${item.report_id}`
    };
  });
}

function transformWatchlist(items) {
  return (items || []).map((item) => ({
    id: item.symbol,
    note: item.note || `${item.name} 已同步到后端观察名单。`
  }));
}

function transformMarketSummary(taskStatus, rankingGroups) {
  const dailyCount = rankingGroups
    .filter((group) => group.frequency === "daily")
    .reduce((sum, group) => sum + (group.rows?.length || 0), 0);
  const weeklyCount = rankingGroups
    .filter((group) => group.frequency === "weekly")
    .reduce((sum, group) => sum + (group.rows?.length || 0), 0);
  return {
    ...mockMarketSummary,
    updatedAt: formatDateTime(taskStatus?.latest_data_update_at),
    nextRefresh: "下个交易日收盘后",
    dailyCount: dailyCount || mockMarketSummary.dailyCount,
    weeklyCount: weeklyCount || mockMarketSummary.weeklyCount,
    dataStatus: "后端 API 已连接",
    marketMood: "API 样例已接入",
    riskTone: "以后端任务状态为准"
  };
}

export async function loadDashboardData({ strategyId, topN = 50 } = {}) {
  const activeStrategyId = strategyId || "momentum_quality_daily";
  const rankingPaths = [
    { market: "cn", frequency: "daily" },
    { market: "hk", frequency: "daily" },
    { market: "cn", frequency: "weekly" },
    { market: "hk", frequency: "weekly" }
  ];
  const [
    macro,
    strategies,
    taskStatus,
    reportsPage,
    watchlistPage,
    ...rankingPages
  ] = await Promise.all([
    apiRequest("/api/macro-regime"),
    apiRequest("/api/strategies"),
    apiRequest("/api/tasks/status"),
    apiRequest("/api/reports?page_size=20"),
    apiRequest("/api/watchlist?page_size=100"),
    ...rankingPaths.map((item) => {
      const params = new URLSearchParams({
        market: item.market,
        frequency: item.frequency,
        top_n: String(topN),
        page_size: String(topN),
        strategy_id: activeStrategyId
      });
      return apiRequest(`/api/rankings?${params.toString()}`);
    })
  ]);

  const reportDetails = await Promise.all(
    (reportsPage || []).map((item) => apiRequest(`/api/reports/${item.report_id}`).catch(() => null))
  );
  const rankingGroups = rankingPaths.map((item, index) => ({
    ...item,
    rows: rankingPages[index] || []
  }));

  return {
    source: "api",
    marketSummary: transformMarketSummary(taskStatus, rankingGroups),
    macroRegime: transformMacroRegime(macro),
    strategyProfiles: transformStrategies(strategies),
    stocks: mergeRankingStocks(rankingGroups),
    reports: transformReports(reportsPage, reportDetails),
    watchlist: transformWatchlist(watchlistPage),
    apiBase: API_BASE
  };
}

export async function addWatchlistItem(symbol, note) {
  return apiRequest("/api/watchlist", {
    method: "POST",
    body: JSON.stringify({ symbol, note })
  });
}

export async function removeWatchlistItem(symbol) {
  return apiRequest(`/api/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE"
  });
}
