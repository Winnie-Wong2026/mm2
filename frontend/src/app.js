import {
  apiContracts,
  backtestSummary,
  researchProfiles,
  macroRegime as mockMacroRegime,
  marketSummary as mockMarketSummary,
  reports as mockReports,
  stocks as mockStocks,
  strategyProfiles as mockStrategyProfiles
} from "./mockData.js";
import {
  addWatchlistItem,
  loadDashboardData,
  removeWatchlistItem
} from "./apiClient.js";

const app = document.querySelector("#app");
const defaultWatchlist = [
  { id: "600519.SH", note: "偏稳健，观察成交额改善能否延续" },
  { id: "00700.HK", note: "港股核心观察池，跟踪连续上榜原因" }
];

let marketSummary = mockMarketSummary;
let macroRegime = mockMacroRegime;
let reports = mockReports;
let stocks = mockStocks;
let strategyProfiles = mockStrategyProfiles;

const state = {
  activeView: "home",
  selectedStockId: "600519.SH",
  selectedReportId: reports[0].id,
  expandedProfessional: false,
  riskFilter: "all",
  rankingFrequency: "daily",
  topN: 20,
  strategyId: loadStrategyId(),
  klineOpen: false,
  klineStockId: null,
  klineFrequency: "daily",
  klineRange: "3m",
  watchlist: loadWatchlist(),
  apiStatus: {
    mode: "loading",
    label: "正在连接后端 API",
    detail: "如果后端不可用，将自动使用本地样例数据。"
  }
};

const views = [
  { id: "home", label: "首页", layer: "第一层", icon: "M3 11l9-8 9 8v10H3V11z" },
  { id: "today", label: "今日精选", layer: "第一层", icon: "M5 5h14v14H5z M8 9h8 M8 13h5" },
  { id: "week", label: "本周精选", layer: "第一层", icon: "M6 4h12v16H6z M9 8h6 M9 12h6 M9 16h3" },
  { id: "watchlist", label: "观察名单", layer: "第一层", icon: "M12 3l2.6 5.3 5.9.9-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.2 5.9-.9z" },
  { id: "detail", label: "股票详情", layer: "第一层", icon: "M4 5h16v14H4z M8 9h8 M8 13h5" },
  { id: "research", label: "研究中心", layer: "第二层", icon: "M4 19V5 M4 19h16 M8 15l3-4 3 2 4-7" },
  { id: "cn", label: "A股榜单", layer: "第二层", icon: "M4 18l5-7 4 3 7-10 M4 20h16" },
  { id: "hk", label: "港股榜单", layer: "第二层", icon: "M4 17l4-5 4 3 8-9 M4 20h16" },
  { id: "reports", label: "报告中心", layer: "第二层", icon: "M6 4h9l3 3v13H6z M14 4v4h4 M9 12h6 M9 16h6" }
];

const klineFrequencyOptions = [
  { id: "daily", label: "日K", stepDays: 1 },
  { id: "weekly", label: "周K", stepDays: 7 },
  { id: "monthly", label: "月K", stepDays: 30 }
];

const klineRangeOptions = [
  { id: "1m", label: "近1月", counts: { daily: 22, weekly: 5, monthly: 2 } },
  { id: "3m", label: "近3月", counts: { daily: 64, weekly: 13, monthly: 3 } },
  { id: "6m", label: "近6月", counts: { daily: 120, weekly: 26, monthly: 6 } },
  { id: "1y", label: "近1年", counts: { daily: 180, weekly: 52, monthly: 12 } }
];

function loadWatchlist() {
  try {
    const saved = JSON.parse(localStorage.getItem("mm2-watchlist") || "null");
    return Array.isArray(saved) ? saved : defaultWatchlist;
  } catch {
    return defaultWatchlist;
  }
}

function saveWatchlist() {
  localStorage.setItem("mm2-watchlist", JSON.stringify(state.watchlist));
}

function loadStrategyId() {
  try {
    const saved = localStorage.getItem("mm2-strategy-id");
    return strategyProfiles.some((strategy) => strategy.id === saved)
      ? saved
      : strategyProfiles[0].id;
  } catch {
    return strategyProfiles[0].id;
  }
}

function saveStrategyId() {
  localStorage.setItem("mm2-strategy-id", state.strategyId);
}

function cnStocks() {
  return stocks.filter((stock) => stock.market === "cn");
}

function hkStocks() {
  return stocks.filter((stock) => stock.market === "hk");
}

function selectedStock() {
  return stocks.find((stock) => stock.id === state.selectedStockId) || stocks[0];
}

function selectedStrategy() {
  return strategyProfiles.find((strategy) => strategy.id === state.strategyId)
    || strategyProfiles[0];
}

function selectedKlineStock() {
  return stocks.find((stock) => stock.id === state.klineStockId) || selectedStock();
}

function selectedReport() {
  return reports.find((report) => report.id === state.selectedReportId) || reports[0];
}

function selectedReportIdIsValid() {
  return reports.some((report) => report.id === state.selectedReportId);
}

function canRunStockSelection() {
  return macroRegime.allowStockSelection;
}

async function hydrateFromApi() {
  try {
    const dashboard = await loadDashboardData({
      strategyId: state.strategyId,
      topN: state.topN
    });
    marketSummary = dashboard.marketSummary;
    macroRegime = dashboard.macroRegime;
    reports = dashboard.reports;
    stocks = dashboard.stocks;
    strategyProfiles = dashboard.strategyProfiles;
    if (dashboard.watchlist.length) {
      state.watchlist = dashboard.watchlist;
      saveWatchlist();
    }
    if (!strategyProfiles.some((strategy) => strategy.id === state.strategyId)) {
      state.strategyId = strategyProfiles[0].id;
      saveStrategyId();
    }
    if (!stocks.some((stock) => stock.id === state.selectedStockId)) {
      state.selectedStockId = stocks[0]?.id || state.selectedStockId;
    }
    if (!selectedReportIdIsValid()) {
      state.selectedReportId = reports[0]?.id || state.selectedReportId;
    }
    state.apiStatus = {
      mode: "api",
      label: "后端 API 已连接",
      detail: `数据来自 ${dashboard.apiBase}`
    };
  } catch (error) {
    state.apiStatus = {
      mode: "mock",
      label: "本地样例数据模式",
      detail: "后端暂不可用，已使用本地样例数据。"
    };
  }
  render();
}

function isWatched(id) {
  return state.watchlist.some((item) => item.id === id);
}

function riskClass(risk) {
  if (risk === "中高") return "risk-mid-high";
  if (risk === "高") return "risk-high";
  if (risk === "低") return "risk-low";
  return "risk-mid";
}

function strategyFactorValue(stock, key) {
  const value = stock.factors[key] || 0;
  const strategy = selectedStrategy();
  if (key === "volatility" && strategy.volatilityMode === "low") return 100 - value;
  if (key === "volatility" && strategy.volatilityMode === "balanced") {
    return 100 - Math.abs(value - 48);
  }
  return value;
}

function strategyAdjustedScore(stock) {
  const strategy = selectedStrategy();
  const entries = Object.entries(strategy.weights || {});
  const totalWeight = entries.reduce((sum, [, weight]) => sum + weight, 0) || 1;
  const factorScore = entries.reduce((sum, [key, weight]) => {
    return sum + strategyFactorValue(stock, key) * weight;
  }, 0) / totalWeight;
  const marketTilt = strategy.marketTilt === "hk"
    ? stock.market === "hk" ? 4 : -2
    : 0;
  const riskPenalty = strategy.volatilityMode === "low" && ["中高", "高"].includes(stock.risk)
    ? 2.5
    : 0;
  const score = stock.score * 0.42 + factorScore * 0.58 + marketTilt - riskPenalty;
  return Math.round(Math.max(45, Math.min(98, score)));
}

function strategyReason(stock) {
  const strategy = selectedStrategy();
  if (strategy.id === strategyProfiles[0].id) return stock.summary;
  const factors = strategy.keyFactors.slice(0, 2).join("、");
  return `${strategy.name}更看重${factors}；${stock.name}当前需注意：${strategy.riskNotes[0]}。`;
}

function strategyRankValue(stock, frequency) {
  const baseRank = frequency === "weekly" ? stock.weeklyRank : stock.dailyRank;
  if (stock.apiRanked?.[frequency]) {
    return 2000 - baseRank * 5 + stock.score;
  }
  return strategyAdjustedScore(stock) * 10 + Math.max(0, 80 - baseRank);
}

function byDailyRank(list) {
  return [...list].sort((a, b) => {
    return strategyRankValue(b, "daily") - strategyRankValue(a, "daily")
      || a.dailyRank - b.dailyRank;
  });
}

function byWeeklyRank(list) {
  return [...list].sort((a, b) => {
    return strategyRankValue(b, "weekly") - strategyRankValue(a, "weekly")
      || a.weeklyRank - b.weeklyRank;
  });
}

function iconPath(path) {
  return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"></path></svg>`;
}

function render() {
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">M2</div>
          <div>
            <div class="brand-title">MM2 研究台</div>
            <div class="brand-subtitle">AI 量化选股原型</div>
          </div>
        </div>
        <nav class="nav-list" aria-label="主导航">
          ${renderNavGroup("第一层", "小白视图")}
          ${renderNavGroup("第二层", "研究视图")}
        </nav>
        <div class="sidebar-note">
          <strong>边界提示</strong>
          <span>所有结果仅用于内部研究参考，页面优先解释原因和风险。</span>
        </div>
      </aside>
      <main class="main-panel">
        ${renderTopbar()}
        ${renderActiveView()}
      </main>
    </div>
    ${state.klineOpen ? renderKlineModal() : ""}
  `;
  bindEvents();
}

function renderNavButton(view) {
  const active = state.activeView === view.id ? "is-active" : "";
  return `
    <button class="nav-button ${active}" data-view="${view.id}" type="button">
      ${iconPath(view.icon)}
      <span>${view.label}</span>
    </button>
  `;
}

function renderNavGroup(layer, title) {
  return `
    <div class="nav-group">
      <div class="nav-group-title">${title}</div>
      ${views.filter((view) => view.layer === layer).map(renderNavButton).join("")}
    </div>
  `;
}

function renderTopbar() {
  return `
    <header class="topbar">
      <div>
        <p class="section-kicker">${state.apiStatus.label}</p>
        <h1>${views.find((view) => view.id === state.activeView)?.label || "首页"}</h1>
      </div>
      <div class="topbar-tools">
        ${renderStrategySwitcher()}
        <div class="topbar-status">
          <span>最近更新：${marketSummary.updatedAt}</span>
          <strong>${marketSummary.dataStatus}</strong>
          <small>${state.apiStatus.detail}</small>
        </div>
      </div>
    </header>
  `;
}

function renderStrategySwitcher() {
  const strategy = selectedStrategy();
  return `
    <div class="strategy-switcher">
      <label class="filter-control">
        当前策略
        <select data-strategy-selector aria-label="更换策略">
          ${strategyProfiles.map((item) => `
            <option value="${item.id}" ${state.strategyId === item.id ? "selected" : ""}>
              ${item.name}
            </option>
          `).join("")}
        </select>
      </label>
      <div class="strategy-switcher-note">
        <strong>${strategy.riskPreference}</strong>
        <span>${strategy.horizon}</span>
      </div>
    </div>
  `;
}

function renderActiveView() {
  if (state.activeView === "today") return renderSelection("daily");
  if (state.activeView === "week") return renderSelection("weekly");
  if (state.activeView === "cn") return renderRanking("cn");
  if (state.activeView === "hk") return renderRanking("hk");
  if (state.activeView === "detail") return renderStockDetail();
  if (state.activeView === "watchlist") return renderWatchlist();
  if (state.activeView === "reports") return renderReports();
  if (state.activeView === "research") return renderResearchCenter();
  return renderHome();
}

function renderHome() {
  const today = byDailyRank(stocks).slice(0, 3);
  const weekly = byWeeklyRank(stocks).slice(0, 3);
  const strategy = selectedStrategy();

  return `
    <section class="home-overview">
      <article class="home-primary">
        <div class="home-primary-head">
          <div>
            <span class="layer-pill">今日决策概览</span>
            <h2>先判断能不能看，再决定看什么。</h2>
            <p>首页只保留四个关键动作：确认宏观状态、选择策略、查看候选、加入观察名单。</p>
          </div>
          <div class="macro-status ${macroRegime.allowStockSelection ? "is-open" : "is-closed"}">
            <span>${macroRegime.status}</span>
            <strong>${macroRegime.confidence}</strong>
            <em>宏观置信度</em>
          </div>
        </div>

        <div class="decision-steps">
          ${renderDecisionStep("01", "宏观状态", macroRegime.regime, macroRegime.status)}
          ${renderDecisionStep("02", "当前策略", strategy.name, strategy.riskPreference)}
          ${renderDecisionStep("03", "仓位上限", macroRegime.positionGuidance.gross, macroRegime.positionGuidance.singleStock)}
          ${renderDecisionStep("04", "下一步", "看候选池", "从今日精选或本周精选进入")}
        </div>

        <div class="home-actions">
          <button class="primary-button" data-view="today" type="button">${iconPath("M5 12h14 M13 6l6 6-6 6")}查看今日精选</button>
          <button class="ghost-button" data-view="week" type="button">${iconPath("M6 4h12v16H6z M9 8h6 M9 12h6 M9 16h3")}查看本周精选</button>
          <button class="ghost-button" data-view="watchlist" type="button">${iconPath("M12 3l2.6 5.3 5.9.9-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.2 5.9-.9z")}观察名单</button>
        </div>
      </article>

      <aside class="home-context">
        ${renderStrategySummaryCard("compact")}
        <div class="home-mini-card">
          <div>
            <span>数据状态</span>
            <strong>${marketSummary.dataStatus}</strong>
          </div>
          <p>最近更新：${marketSummary.updatedAt}；下次更新：${marketSummary.nextRefresh}。</p>
          <div class="mini-metrics">
            <span><strong>${marketSummary.dailyCount}</strong>今日样例</span>
            <span><strong>${marketSummary.weeklyCount}</strong>本周样例</span>
            <span><strong>${state.watchlist.length}</strong>已观察</span>
          </div>
        </div>
      </aside>
    </section>

    <section class="home-workbench">
      <article class="candidate-board">
        <div class="section-title">
          <div>
            <h3>候选股工作台</h3>
            <p>先看 Top 3，完整列表再进入对应页面。</p>
          </div>
          <button class="link-button" data-view="today" type="button">查看全部候选</button>
        </div>
        <div class="candidate-columns">
          <div class="candidate-list">
            <div class="candidate-list-head">
              <strong>今日精选</strong>
              <button class="link-button" data-view="today" type="button">日频榜单</button>
            </div>
            ${today.map((stock, index) => renderHomeCandidateRow(stock, "daily", index + 1)).join("")}
          </div>
          <div class="candidate-list">
            <div class="candidate-list-head">
              <strong>本周精选</strong>
              <button class="link-button" data-view="week" type="button">周频榜单</button>
            </div>
            ${weekly.map((stock, index) => renderHomeCandidateRow(stock, "weekly", index + 1)).join("")}
          </div>
        </div>
      </article>

      <aside class="market-focus-panel">
        <div class="section-title">
          <h3>板块与风险</h3>
        </div>
        <div class="sector-focus-list">
          ${macroRegime.sectorAllocation.slice(0, 4).map((item, index) => renderSectorFocus(item, index)).join("")}
        </div>
        <div class="risk-note-list">
          ${macroRegime.riskReminders.slice(0, 2).map((item) => `<p>${item}</p>`).join("")}
        </div>
      </aside>
    </section>

    <section class="research-strip">
      <div class="section-title">
        <div>
          <span class="layer-pill muted">第二层：研究人员看</span>
          <h3>需要深挖时再进入研究层</h3>
        </div>
        <button class="link-button" data-view="research" type="button">进入研究中心</button>
      </div>
      <div class="research-entry-grid">
        <span>因子明细</span>
        <span>历史回测</span>
        <span>收益曲线</span>
        <span>最大回撤</span>
        <span>胜率</span>
        <span>换手率</span>
        <span>行业暴露</span>
        <span>模型解释</span>
      </div>
    </section>
  `;
}

function renderDecisionStep(number, label, title, detail) {
  return `
    <div class="decision-step">
      <span>${number}</span>
      <strong>${label}</strong>
      <h3>${title}</h3>
      <p>${detail}</p>
    </div>
  `;
}

function renderHomeCandidateRow(stock, type, rank) {
  const watched = isWatched(stock.id);
  const score = strategyAdjustedScore(stock);
  const reason = strategyReason(stock);
  return `
    <div class="candidate-row">
      <span class="candidate-rank">#${rank}</span>
      <div class="candidate-main">
        <div>
          <span class="market-badge">${stock.board}</span>
          <h3>${stock.name}</h3>
          <small>${stock.symbol} · ${stock.industry}</small>
        </div>
        <p>${reason}</p>
      </div>
      <div class="candidate-score">
        <strong>${score}</strong>
        <em class="${riskClass(stock.risk)}">${stock.risk}</em>
      </div>
      <div class="candidate-actions">
        <button class="ghost-button small" data-stock="${stock.id}" data-view="detail" type="button">详情</button>
        <button class="ghost-button small" data-kline="${stock.id}" type="button">K线</button>
        <button class="primary-button small" data-watch="${stock.id}" type="button">${watched ? "已观察" : "观察"}</button>
      </div>
    </div>
  `;
}

function renderSectorFocus(item, index) {
  return `
    <div class="sector-focus-row">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <div>
        <strong>${item.name}</strong>
        <small>${item.stance} · ${item.reason}</small>
      </div>
      <em>${item.target}</em>
    </div>
  `;
}

function renderStrategySummaryCard(variant = "") {
  const strategy = selectedStrategy();
  const className = variant ? `strategy-card ${variant}` : "strategy-card";
  return `
    <div class="${className}">
      <div class="layer-card-head">
        <span>当前策略</span>
        <strong>${strategy.name}</strong>
      </div>
      <p>${strategy.description}</p>
      <div class="strategy-meta-grid">
        <span><strong>风险偏好</strong>${strategy.riskPreference}</span>
        <span><strong>观察周期</strong>${strategy.horizon}</span>
        <span><strong>覆盖市场</strong>${strategy.universe}</span>
      </div>
      <div class="strategy-factor-list">
        ${strategy.keyFactors.map((item) => `<span>${item}</span>`).join("")}
      </div>
    </div>
  `;
}

function renderSelection(type) {
  const isDaily = type === "daily";
  const title = isDaily ? "今日精选候选股" : "本周精选候选股";
  const helper = isDaily
    ? "日频结果更关注收盘后的短中期变化，适合每天快速浏览。"
    : "周频结果更关注连续性，适合每周复盘和更新观察名单。";
  const ranked = isDaily ? byDailyRank(stocks) : byWeeklyRank(stocks);
  const strategy = selectedStrategy();
  const canSelect = canRunStockSelection();

  return `
    <section class="page-intro">
      <div>
        <h2>${title}</h2>
        <p>${helper} 当前策略：${strategy.name}。宏观状态：${macroRegime.status}。</p>
      </div>
      <div class="notice-strip">策略参数：${strategy.apiHint}</div>
    </section>
    <section class="stock-grid">
      ${canSelect ? ranked
        .slice(0, 8)
        .map((stock, index) => renderStockCard(stock, type, index + 1))
        .join("") : renderMacroBlockedState()}
    </section>
  `;
}

function renderRanking(market) {
  const list = market === "cn" ? cnStocks() : hkStocks();
  const title = market === "cn" ? "A股榜单" : "港股榜单";
  const filtered = state.riskFilter === "all"
    ? list
    : list.filter((stock) => stock.risk === state.riskFilter);
  const rankedAll = state.rankingFrequency === "weekly"
    ? byWeeklyRank(filtered)
    : byDailyRank(filtered);
  const ranked = rankedAll.slice(0, state.topN);
  const frequencyLabel = state.rankingFrequency === "weekly" ? "周频" : "日频";
  const strategy = selectedStrategy();
  const canSelect = canRunStockSelection();

  return `
    <section class="page-intro ranking-intro">
      <div>
        <span class="layer-pill muted">第二层：研究人员看</span>
        <h2>${title}</h2>
        <p>
          ${macroRegime.status}后展示 ${frequencyLabel} Top ${state.topN}，
          已按“${strategy.name}”重排。
        </p>
      </div>
      <div class="ranking-controls">
        <label class="filter-control">
          榜单周期
          <select data-ranking-frequency>
            <option value="daily" ${state.rankingFrequency === "daily" ? "selected" : ""}>
              日频
            </option>
            <option value="weekly" ${state.rankingFrequency === "weekly" ? "selected" : ""}>
              周频
            </option>
          </select>
        </label>
        <label class="filter-control">
          输出数量
          <select data-top-n>
            <option value="20" ${state.topN === 20 ? "selected" : ""}>Top 20</option>
            <option value="50" ${state.topN === 50 ? "selected" : ""}>Top 50</option>
          </select>
        </label>
        <label class="filter-control">
          风险筛选
          <select data-risk-filter>
            <option value="all" ${state.riskFilter === "all" ? "selected" : ""}>全部</option>
            <option value="低" ${state.riskFilter === "低" ? "selected" : ""}>低</option>
            <option value="中" ${state.riskFilter === "中" ? "selected" : ""}>中</option>
            <option value="中高" ${state.riskFilter === "中高" ? "selected" : ""}>中高</option>
            <option value="高" ${state.riskFilter === "高" ? "selected" : ""}>高</option>
          </select>
        </label>
      </div>
    </section>
    <section class="ranking-table" aria-label="${title}">
      <div class="ranking-row ranking-head">
        <span>排名</span><span>股票</span><span>评分</span><span>风险</span>
        <span>观察周期</span><span>入选理由</span><span>操作</span>
      </div>
      ${canSelect && ranked.length
        ? ranked.map((stock, index) => renderRankingRow(stock, index + 1)).join("")
        : renderEmptyRanking()}
    </section>
  `;
}

function renderResearchCenter() {
  const stock = selectedStock();
  const score = strategyAdjustedScore(stock);
  return `
    <section class="page-intro">
      <div>
        <span class="layer-pill muted">第二层：研究人员看</span>
        <h2>研究中心</h2>
        <p>因子明细、历史回测、收益曲线、回撤、胜率、换手率、行业暴露和模型解释都集中放在这里。</p>
      </div>
      <div class="notice-strip">${backtestSummary.status} · ${backtestSummary.period}</div>
    </section>
    <section class="detail-shell">
      <aside class="stock-picker">
        <h2>研究对象</h2>
        ${stocks.map((item) => `
          <button class="stock-picker-row ${item.id === stock.id ? "is-selected" : ""}" data-stock="${item.id}" type="button">
            <span>${item.name}</span>
            <small>${item.symbol}</small>
          </button>
        `).join("")}
      </aside>
      <article class="detail-panel research-panel">
        <div class="detail-head">
          <div>
            <span class="market-badge">${stock.board}</span>
            <h2>${stock.name} <small>${stock.symbol}</small></h2>
            <p>${backtestSummary.benchmark}，接口路径 ${backtestSummary.apiHint}。</p>
          </div>
          <div class="score-block">
            <span>研究样本</span>
            <strong>${score}</strong>
            <em>综合评分</em>
          </div>
        </div>
        ${renderResearchDetails(stock)}
      </article>
    </section>
  `;
}

function renderStockDetail() {
  const stock = selectedStock();
  const watched = isWatched(stock.id);
  const score = strategyAdjustedScore(stock);
  return `
    <section class="detail-shell">
      <aside class="stock-picker">
        <h2>选择股票</h2>
        ${stocks.map((item) => `
          <button class="stock-picker-row ${item.id === stock.id ? "is-selected" : ""}" data-stock="${item.id}" type="button">
            <span>${item.name}</span>
            <small>${item.symbol}</small>
          </button>
        `).join("")}
      </aside>
      <article class="detail-panel">
        <span class="layer-pill">第一层：小白看</span>
        <div class="detail-head">
          <div>
            <span class="market-badge">${stock.board}</span>
            <h2>${stock.name} <small>${stock.symbol}</small></h2>
            <p>${stock.summary}</p>
          </div>
          <div class="score-block">
            <span>AI 综合评分</span>
            <strong>${score}</strong>
            <em class="${riskClass(stock.risk)}">风险 ${stock.risk}</em>
          </div>
        </div>

        <div class="novice-answer-grid">
          <section>
            <h3>为什么上榜</h3>
            <p>${stock.summary}</p>
            <div class="reason-list">${stock.strengths.map((item) => `<span>${item}</span>`).join("")}</div>
          </section>
          <section>
            <h3>适合观察多久</h3>
            <p>${stock.horizon}</p>
            <span class="soft-label">连续 ${stock.consecutive} 期进入候选池</span>
          </section>
          <section>
            <h3>主要风险是什么</h3>
            <p>${stock.risks[0]}</p>
            <div class="reason-list">${stock.risks.slice(1).map((item) => `<span>${item}</span>`).join("")}</div>
          </section>
          <section>
            <h3>是否进入观察名单</h3>
            <p>${watched ? "已在观察名单中，后续复盘时优先查看。" : "还未加入观察名单，可以先收藏后再复盘。"}</p>
            <button class="${watched ? "ghost-button" : "primary-button"} small" data-watch="${stock.id}" type="button">
              ${watched ? "移出观察" : "加入观察"}
            </button>
          </section>
        </div>

        <section class="professional-panel">
          <button class="disclosure-button" data-toggle-professional type="button">
            ${iconPath("M6 9l6 6 6-6")}
            ${state.expandedProfessional ? "收起研究人员视图" : "展开研究人员视图"}
          </button>
          ${state.expandedProfessional ? renderResearchDetails(stock) : ""}
        </section>
      </article>
    </section>
  `;
}

function renderWatchlist() {
  const watched = state.watchlist
    .map((item) => ({ ...item, stock: stocks.find((stock) => stock.id === item.id) }))
    .filter((item) => item.stock);

  return `
    <section class="page-intro">
      <div>
        <h2>我的观察名单</h2>
        <p>收藏候选股并记录观察理由，后续由 <code>/api/watchlist</code> 持久化到用户账号。</p>
      </div>
      <div class="notice-strip">已观察 ${watched.length} 只</div>
    </section>
    <section class="watchlist-layout">
      <div class="watchlist-items">
        ${watched.length ? watched.map(renderWatchItem).join("") : renderEmptyWatchlist()}
      </div>
      <aside class="api-panel">
        <h3>后续 API 对接点</h3>
        ${apiContracts.map((item) => `
          <div class="api-row">
            <strong>${item.page}</strong>
            <code>${item.endpoint}</code>
            <span>${item.fields}</span>
          </div>
        `).join("")}
      </aside>
    </section>
  `;
}

function renderReports() {
  const report = selectedReport();
  return `
    <section class="reports-layout">
      <aside class="report-list">
        <span class="layer-pill muted">第二层：研究人员看</span>
        <h2>报告中心</h2>
        ${reports.map((item) => `
          <button class="report-item ${item.id === report.id ? "is-selected" : ""}" data-report="${item.id}" type="button">
            <span>${item.title}</span>
            <small>${item.type} · ${item.date}</small>
          </button>
        `).join("")}
      </aside>
      <article class="report-detail">
        <div class="detail-head">
          <div>
            <span class="market-badge">${report.type}</span>
            <h2>${report.title}</h2>
            <p>${report.summary}</p>
          </div>
          <div class="report-status">
            <span>${report.status}</span>
            <code>${report.apiHint}</code>
          </div>
        </div>
        <div class="report-sections">
          ${report.sections.map((section, index) => `
            <section>
              <span>${String(index + 1).padStart(2, "0")}</span>
              <h3>${section}</h3>
              <p>这里展示面向小白用户的中文解释，并保留专业指标入口。</p>
            </section>
          `).join("")}
        </div>
      </article>
    </section>
  `;
}

function renderStockCard(stock, type, rankOverride) {
  const rank = rankOverride || (type === "weekly" ? stock.weeklyRank : stock.dailyRank);
  const watched = isWatched(stock.id);
  const score = strategyAdjustedScore(stock);
  const reason = strategyReason(stock);
  return `
    <article class="stock-card">
      <div class="card-head">
        <div>
          <span class="market-badge">${stock.board}</span>
          <h3>${stock.name}</h3>
          <small>${stock.symbol} · ${stock.industry}</small>
        </div>
        <div class="rank-chip">#${rank}</div>
      </div>
      <div class="score-risk-row">
        <div>
          <span>AI 综合评分</span>
          <strong>${score}</strong>
        </div>
        <div>
          <span>风险等级</span>
          <strong class="${riskClass(stock.risk)}">${stock.risk}</strong>
        </div>
      </div>
      <div class="card-answer-grid">
        <div>
          <span>为什么上榜</span>
          <p>${reason}</p>
        </div>
        <div>
          <span>适合观察多久</span>
          <p>${stock.horizon}</p>
        </div>
        <div>
          <span>主要风险是什么</span>
          <p>${stock.risks[0]}</p>
        </div>
        <div>
          <span>是否进入观察名单</span>
          <p>${watched ? "已进入观察名单" : "还未观察"}</p>
        </div>
      </div>
      <div class="card-actions">
        <button class="ghost-button small" data-stock="${stock.id}" data-view="detail" type="button">看小白详情</button>
        <button class="ghost-button small" data-kline="${stock.id}" type="button">查看K线</button>
        <button class="primary-button small" data-watch="${stock.id}" type="button">${watched ? "已在观察" : "加入观察"}</button>
      </div>
    </article>
  `;
}

function renderRankingRow(stock, rank) {
  const watched = isWatched(stock.id);
  const score = strategyAdjustedScore(stock);
  const reason = strategyReason(stock);
  return `
    <div class="ranking-row">
      <span class="rank-number">${rank}</span>
      <span class="stock-name-cell"><strong>${stock.name}</strong><small>${stock.symbol} · ${stock.industry}</small></span>
      <span>${score}</span>
      <span class="${riskClass(stock.risk)}">风险 ${stock.risk}</span>
      <span>${stock.horizon}</span>
      <span>${reason}</span>
      <span class="row-actions">
        <button class="icon-button" data-stock="${stock.id}" data-view="detail" type="button" aria-label="查看详情">${iconPath("M4 5h16v14H4z M8 9h8 M8 13h5")}</button>
        <button class="icon-button ${watched ? "is-on" : ""}" data-watch="${stock.id}" type="button" aria-label="加入观察">${iconPath("M12 3l2.6 5.3 5.9.9-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.2 5.9-.9z")}</button>
      </span>
    </div>
  `;
}

function renderWatchItem(item) {
  const stock = item.stock;
  const score = strategyAdjustedScore(stock);
  return `
    <article class="watch-item">
      <div>
        <span class="market-badge">${stock.board}</span>
        <h3>${stock.name}</h3>
        <p>${item.note}</p>
      </div>
      <div class="watch-meta">
        <strong>${score}</strong>
        <span class="${riskClass(stock.risk)}">风险 ${stock.risk}</span>
        <button class="link-button" data-remove-watch="${stock.id}" type="button">移出</button>
      </div>
    </article>
  `;
}

function renderEmptyWatchlist() {
  return `
    <div class="empty-state">
      <h3>观察名单为空</h3>
      <p>可以从今日精选或榜单中加入候选股，后续跟踪它是否仍在榜单中。</p>
    </div>
  `;
}

function renderEmptyRanking() {
  if (!canRunStockSelection()) {
    return renderMacroBlockedState();
  }
  return `
    <div class="empty-state ranking-empty">
      <h3>当前筛选暂无样例</h3>
      <p>可以切换风险等级、榜单周期或 Top 数量查看其他 mock 候选股。</p>
    </div>
  `;
}

function renderMacroBlockedState() {
  return `
    <div class="empty-state ranking-empty">
      <h3>宏观状态暂不支持进入个股筛选</h3>
      <p>先复核宏观风险、板块方向和仓位上限；大方向恢复后再输出候选股。</p>
    </div>
  `;
}

function researchProfile(stock) {
  const profile = researchProfiles[stock.id] || researchProfiles.default;
  const industryExposure = profile.industryExposure?.length
    ? profile.industryExposure
    : [
      { name: stock.industry, weight: 38 },
      { name: "相关行业", weight: 27 },
      { name: "其他", weight: 35 }
    ];
  return { ...profile, industryExposure };
}

function renderResearchDetails(stock) {
  const profile = researchProfile(stock);
  return `
    <div class="research-sections">
      <section class="research-section">
        <div class="section-title">
          <h3>因子明细</h3>
          <span class="soft-label">trend / liquidity / valuation / quality / volatility</span>
        </div>
        ${renderFactorDetails(stock)}
      </section>

      <section class="research-section">
        <div class="section-title">
          <h3>历史回测</h3>
          <span class="soft-label">${profile.backtestPeriod}</span>
        </div>
        <div class="research-metric-grid">
          <div><span>累计收益</span><strong>${profile.cumulativeReturn}</strong></div>
          <div><span>最大回撤</span><strong>${profile.maxDrawdown}</strong></div>
          <div><span>胜率</span><strong>${profile.winRate}</strong></div>
          <div><span>换手率</span><strong>${profile.turnover}</strong></div>
        </div>
      </section>

      <section class="research-section">
        <div class="section-title">
          <h3>收益曲线</h3>
          <span class="soft-label">mock 曲线，等待回测线程接入真实结果</span>
        </div>
        ${renderMiniChart(profile.equityCurve)}
      </section>

      <section class="research-section">
        <div class="section-title">
          <h3>行业暴露</h3>
          <span class="soft-label">用于检查候选池是否过度集中</span>
        </div>
        <div class="industry-exposure-list">
          ${profile.industryExposure.map(renderIndustryExposure).join("")}
        </div>
      </section>

      <section class="research-section full">
        <div class="section-title">
          <h3>模型解释</h3>
          <span class="soft-label">正式版本由策略解释模块返回</span>
        </div>
        <div class="model-explain-list">
          ${profile.modelExplanation.map((item) => `<span>${item}</span>`).join("")}
        </div>
      </section>
    </div>
  `;
}

function renderIndustryExposure(item) {
  return `
    <div class="industry-exposure-row">
      <span>${item.name}</span>
      <div class="factor-bar"><i style="width: ${item.weight}%"></i></div>
      <strong>${item.weight}%</strong>
    </div>
  `;
}

function klineFrequencyOption() {
  return klineFrequencyOptions.find((option) => option.id === state.klineFrequency) || klineFrequencyOptions[0];
}

function klineRangeOption() {
  return klineRangeOptions.find((option) => option.id === state.klineRange) || klineRangeOptions[1];
}

function formatKlineDate(date, frequency) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return frequency === "monthly" ? `${year}-${month}` : `${year}-${month}-${day}`;
}

function candleCount() {
  const range = klineRangeOption();
  return range.counts[state.klineFrequency] || range.counts.daily;
}

function riskVolatility(risk) {
  if (risk === "高") return 0.055;
  if (risk === "中高") return 0.038;
  if (risk === "低") return 0.014;
  return 0.024;
}

function buildCandleSeries(stock) {
  const count = candleCount();
  const option = klineFrequencyOption();
  const seed = [...stock.id].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  const frequencyMultiplier = state.klineFrequency === "monthly" ? 2.4 : state.klineFrequency === "weekly" ? 1.55 : 1;
  const volatility = riskVolatility(stock.risk) * frequencyMultiplier;
  const latest = new Date("2026-05-22T00:00:00");
  const score = strategyAdjustedScore(stock);
  let close = stock.priceSeries[0] + score / 18;

  return Array.from({ length: count }, (_, index) => {
    const date = new Date(latest);
    date.setDate(latest.getDate() - (count - index - 1) * option.stepDays);
    const wave = Math.sin((seed + index) * 0.73);
    const pulse = Math.cos((seed + index) * 0.41);
    const open = close * (1 + wave * volatility * 0.42);
    const drift = (score - 76) / 2200;
    const nextClose = Math.max(1, open * (1 + drift + pulse * volatility * 0.56));
    const high = Math.max(open, nextClose) * (1 + (0.009 + Math.abs(wave) * volatility * 0.34));
    const low = Math.min(open, nextClose) * (1 - (0.009 + Math.abs(pulse) * volatility * 0.34));
    close = nextClose;

    return {
      date: formatKlineDate(date, state.klineFrequency),
      open,
      close: nextClose,
      high,
      low,
      volume: Math.round((score * 1200 + seed * 9 + index * 137) * frequencyMultiplier)
    };
  });
}

function renderKlineModal() {
  const stock = selectedKlineStock();
  const score = strategyAdjustedScore(stock);
  const candles = buildCandleSeries(stock);
  const latest = candles[candles.length - 1];
  const previous = candles[candles.length - 2] || latest;
  const change = latest.close - previous.close;
  const changePct = previous.close ? (change / previous.close) * 100 : 0;
  const up = latest.close >= latest.open;

  return `
    <div class="kline-backdrop" role="presentation">
      <section class="kline-modal" role="dialog" aria-modal="true" aria-label="${stock.name} K线详情">
        <header class="kline-modal-head">
          <div>
            <span class="market-badge">${stock.board}</span>
            <h2>${stock.name} <small>${stock.symbol}</small></h2>
            <p>${stock.summary}</p>
          </div>
          <button class="icon-button" data-close-kline type="button" aria-label="关闭K线弹窗">${iconPath("M6 6l12 12 M18 6L6 18")}</button>
        </header>

        <div class="kline-controls">
          <label class="filter-control">
            K线周期
            <select data-kline-frequency>
              ${klineFrequencyOptions.map((option) => `
                <option value="${option.id}" ${state.klineFrequency === option.id ? "selected" : ""}>${option.label}</option>
              `).join("")}
            </select>
          </label>
          <label class="filter-control">
            时间区间
            <select data-kline-range>
              ${klineRangeOptions.map((option) => `
                <option value="${option.id}" ${state.klineRange === option.id ? "selected" : ""}>${option.label}</option>
              `).join("")}
            </select>
          </label>
          <div class="kline-legend">
            <span><i class="legend-up"></i>红涨</span>
            <span><i class="legend-down"></i>绿跌</span>
          </div>
        </div>

        <div class="kline-layout">
          <aside class="kline-info">
            <div class="score-risk-row">
              <div>
                <span>AI 综合评分</span>
                <strong>${score}</strong>
              </div>
              <div>
                <span>风险等级</span>
                <strong class="${riskClass(stock.risk)}">${stock.risk}</strong>
              </div>
            </div>
            <dl class="kline-quote">
              <div><dt>最新收盘</dt><dd class="${up ? "price-up" : "price-down"}">${latest.close.toFixed(2)}</dd></div>
              <div><dt>区间涨跌</dt><dd class="${change >= 0 ? "price-up" : "price-down"}">${change >= 0 ? "+" : ""}${change.toFixed(2)} / ${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%</dd></div>
              <div><dt>最高</dt><dd>${latest.high.toFixed(2)}</dd></div>
              <div><dt>最低</dt><dd>${latest.low.toFixed(2)}</dd></div>
              <div><dt>成交量</dt><dd>${latest.volume.toLocaleString("zh-CN")}</dd></div>
            </dl>
            <div class="kline-detail-list">
              <span>为什么上榜：${stock.summary}</span>
              <span>适合观察：${stock.horizon}</span>
              <span>主要风险：${stock.risks[0]}</span>
            </div>
          </aside>
          <article class="kline-chart-panel">
            <div class="section-title">
              <h3>${klineFrequencyOption().label} · ${klineRangeOption().label}</h3>
              <span class="soft-label">mock K线，红涨绿跌</span>
            </div>
            ${renderCandlestickChart(candles)}
          </article>
        </div>
      </section>
    </div>
  `;
}

function renderCandlestickChart(candles) {
  const high = Math.max(...candles.map((item) => item.high));
  const low = Math.min(...candles.map((item) => item.low));
  const span = Math.max(1, high - low);
  const labelStep = Math.max(1, Math.ceil(candles.length / 6));

  return `
    <div class="candlestick-wrap">
      <div class="price-axis">
        <span>${high.toFixed(2)}</span>
        <span>${((high + low) / 2).toFixed(2)}</span>
        <span>${low.toFixed(2)}</span>
      </div>
      <div class="candlestick-scroll">
        <div class="candlestick-chart" style="min-width: ${Math.max(520, candles.length * 15)}px;">
          ${candles.map((item, index) => {
            const up = item.close >= item.open;
            const highTop = ((high - item.high) / span) * 100;
            const lowTop = ((high - item.low) / span) * 100;
            const openTop = ((high - item.open) / span) * 100;
            const closeTop = ((high - item.close) / span) * 100;
            const bodyTop = Math.min(openTop, closeTop);
            const bodyHeight = Math.max(2, Math.abs(closeTop - openTop));
            const label = index % labelStep === 0 || index === candles.length - 1 ? item.date : "";
            return `
              <div class="candle-slot" title="${item.date} 开 ${item.open.toFixed(2)} 高 ${item.high.toFixed(2)} 低 ${item.low.toFixed(2)} 收 ${item.close.toFixed(2)}">
                <span class="candle ${up ? "is-up" : "is-down"}" style="--wick-top: ${highTop}%; --wick-height: ${Math.max(2, lowTop - highTop)}%; --body-top: ${bodyTop}%; --body-height: ${bodyHeight}%;"></span>
                <em>${label}</em>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    </div>
  `;
}

function renderSector(sector) {
  return `
    <div class="sector-row">
      <div>
        <strong>${sector.name}</strong>
        <span>${sector.tone} · ${sector.risk}</span>
      </div>
      <div class="heat-bar" aria-label="${sector.name} 热度 ${sector.heat}">
        <span style="width: ${sector.heat}%"></span>
      </div>
      <em>${sector.heat}</em>
    </div>
  `;
}

function renderMiniChart(series) {
  const max = Math.max(...series);
  const min = Math.min(...series);
  return `
    <div class="mini-chart">
      ${series.map((value) => {
        const height = 28 + ((value - min) / Math.max(1, max - min)) * 72;
        return `<span style="height: ${height}%"></span>`;
      }).join("")}
    </div>
  `;
}

function renderFactorDetails(stock) {
  const labels = {
    trend: "趋势动量",
    liquidity: "成交活跃",
    valuation: "估值位置",
    quality: "质量评分",
    volatility: "波动风险"
  };

  return `
    <div class="factor-grid">
      ${Object.entries(stock.factors).map(([key, value]) => `
        <div class="factor-row">
          <span>${labels[key]}</span>
          <div class="factor-bar"><i style="width: ${value}%"></i></div>
          <strong>${value}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function bindEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const stockId = button.getAttribute("data-stock");
      if (stockId) state.selectedStockId = stockId;
      state.activeView = button.getAttribute("data-view") || "home";
      render();
    });
  });

  document.querySelectorAll("[data-stock]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedStockId = button.getAttribute("data-stock") || state.selectedStockId;
      if (!button.hasAttribute("data-view")) render();
    });
  });

  document.querySelectorAll("[data-kline]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.getAttribute("data-kline");
      if (!id) return;
      state.klineStockId = id;
      state.selectedStockId = id;
      state.klineOpen = true;
      render();
    });
  });

  document.querySelectorAll("[data-close-kline]").forEach((button) => {
    button.addEventListener("click", () => {
      state.klineOpen = false;
      render();
    });
  });

  document.querySelectorAll("[data-watch]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.getAttribute("data-watch");
      if (!id) return;
      const previous = [...state.watchlist];
      if (isWatched(id)) {
        state.watchlist = state.watchlist.filter((item) => item.id !== id);
        if (state.apiStatus.mode === "api") {
          removeWatchlistItem(id).catch(() => {
            state.watchlist = previous;
            saveWatchlist();
            render();
          });
        }
      } else {
        const stock = stocks.find((item) => item.id === id);
        const note = `${stock?.name || id} 已加入观察，等待下一期榜单更新后复核。`;
        state.watchlist = [
          ...state.watchlist,
          { id, note }
        ];
        if (state.apiStatus.mode === "api") {
          addWatchlistItem(id, note).catch(() => {
            state.watchlist = previous;
            saveWatchlist();
            render();
          });
        }
      }
      saveWatchlist();
      render();
    });
  });

  document.querySelectorAll("[data-remove-watch]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.getAttribute("data-remove-watch");
      const previous = [...state.watchlist];
      state.watchlist = state.watchlist.filter((item) => item.id !== id);
      if (state.apiStatus.mode === "api") {
        removeWatchlistItem(id).catch(() => {
          state.watchlist = previous;
          saveWatchlist();
          render();
        });
      }
      saveWatchlist();
      render();
    });
  });

  document.querySelectorAll("[data-report]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedReportId = button.getAttribute("data-report") || state.selectedReportId;
      render();
    });
  });

  const filter = document.querySelector("[data-risk-filter]");
  if (filter) {
    filter.addEventListener("change", (event) => {
      state.riskFilter = event.target.value;
      render();
    });
  }

  const frequency = document.querySelector("[data-ranking-frequency]");
  if (frequency) {
    frequency.addEventListener("change", (event) => {
      state.rankingFrequency = event.target.value;
      render();
    });
  }

  const topN = document.querySelector("[data-top-n]");
  if (topN) {
    topN.addEventListener("change", (event) => {
      state.topN = Number(event.target.value);
      render();
    });
  }

  const strategySelector = document.querySelector("[data-strategy-selector]");
  if (strategySelector) {
    strategySelector.addEventListener("change", (event) => {
      state.strategyId = event.target.value;
      saveStrategyId();
      state.apiStatus = {
        ...state.apiStatus,
        detail: state.apiStatus.mode === "api" ? "正在刷新该策略的后端榜单..." : state.apiStatus.detail
      };
      render();
      if (state.apiStatus.mode === "api") hydrateFromApi();
    });
  }

  const klineFrequency = document.querySelector("[data-kline-frequency]");
  if (klineFrequency) {
    klineFrequency.addEventListener("change", (event) => {
      state.klineFrequency = event.target.value;
      render();
    });
  }

  const klineRange = document.querySelector("[data-kline-range]");
  if (klineRange) {
    klineRange.addEventListener("change", (event) => {
      state.klineRange = event.target.value;
      render();
    });
  }

  const professional = document.querySelector("[data-toggle-professional]");
  if (professional) {
    professional.addEventListener("click", () => {
      state.expandedProfessional = !state.expandedProfessional;
      render();
    });
  }
}

render();
hydrateFromApi();
