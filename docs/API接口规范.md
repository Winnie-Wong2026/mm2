# API 接口规范

## 1. 基础原则

后端使用 FastAPI。第一阶段先返回 mock 数据，但接口结构必须为后续真实数据、策略评分、报告生成和前端页面保留稳定字段。

当前后端平台线程只负责：

- 登录、当前用户、角色权限骨架
- 宏观状态、板块方向、仓位配置和风险提醒 API
- 当前榜单和股票详情 API
- 可选策略列表 API
- 用户观察名单 API
- 报告列表和报告详情 API
- 数据更新、榜单生成、报告生成等任务状态 API

不在本接口层直接实现数据源、因子、策略、评分模型和交易执行。

## 2. 基础约定

### 2.1 API 前缀

所有业务接口统一使用：

```text
/api
```

健康检查可使用：

```text
/health
```

### 2.2 统一响应结构

成功响应：

```json
{
  "data": {},
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

列表响应：

```json
{
  "data": [],
  "meta": {
    "request_id": "mock-request",
    "mock": true,
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 2
    }
  }
}
```

错误响应：

```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "用户名或密码不正确",
    "details": {}
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

### 2.3 鉴权方式

第一阶段使用 mock token：

```text
Authorization: Bearer mock-token-{username}
```

登录接口返回 token。除 `/api/auth/login` 和 `/health` 外，其他接口默认需要 Bearer token。

### 2.4 角色

| 角色 | 说明 | 第一阶段权限 |
| --- | --- | --- |
| `admin` | 管理员 | 查看所有接口、任务状态和后续用户管理 |
| `researcher` | 研究员 | 查看榜单、详情、报告、模型解释和任务状态 |
| `viewer` | 普通用户 | 查看榜单、详情、报告和自己的观察名单 |

第一阶段预置 mock 用户：

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `admin123` | `admin` |
| `researcher` | `research123` | `researcher` |
| `viewer` | `viewer123` | `viewer` |

### 2.5 枚举字段

| 字段 | 可选值 | 说明 |
| --- | --- | --- |
| `market` | `cn`, `hk` | A股、港股 |
| `frequency` | `daily`, `weekly` | 日频、周频 |
| `top_n` | `20`, `50` | Top 20 或 Top 50 |
| `risk_level` | `低`, `中`, `中高`, `高` | 小白用户可理解的风险等级 |
| `horizon` | `5日`, `10日`, `20日`, `4周`, `8周`, `12周` | 观察周期 |

### 2.6 分页参数

列表接口统一保留：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `page` | int | `1` | 页码，从 1 开始 |
| `page_size` | int | `20` | 每页数量，第一阶段最大 100 |

第一阶段 mock 数据量较小，也按分页结构返回。

### 2.7 本地运行约定

后端依赖统一写入根目录 `pyproject.toml`。第一阶段建议使用 Python 3.11 及以上环境启动：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8000
```

本地启动后：

- 健康检查：`GET http://127.0.0.1:8000/health`
- API 文档：`http://127.0.0.1:8000/docs`
- 前端联调默认使用 `Authorization: Bearer mock-token-{username}`

## 3. 错误码

| HTTP 状态码 | code | 说明 |
| --- | --- | --- |
| 400 | `COMMON_BAD_REQUEST` | 请求参数不合法 |
| 401 | `AUTH_REQUIRED` | 缺少或未提供有效 token |
| 401 | `AUTH_INVALID_CREDENTIALS` | 用户名或密码不正确 |
| 403 | `AUTH_FORBIDDEN` | 当前角色无权访问 |
| 404 | `RESOURCE_NOT_FOUND` | 资源不存在 |
| 409 | `WATCHLIST_ALREADY_EXISTS` | 观察名单中已存在该股票 |
| 500 | `COMMON_INTERNAL_ERROR` | 服务内部错误 |

## 4. 接口定义

### 4.1 健康检查

```text
GET /health
```

响应：

```json
{
  "status": "ok",
  "service": "mm2-backend",
  "mock": true
}
```

### 4.2 登录

```text
POST /api/auth/login
```

请求：

```json
{
  "username": "viewer",
  "password": "viewer123"
}
```

响应：

```json
{
  "data": {
    "access_token": "mock-token-viewer",
    "token_type": "bearer",
    "user": {
      "user_id": "u_viewer",
      "username": "viewer",
      "display_name": "普通用户",
      "role": "viewer"
    }
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

### 4.3 当前用户

```text
GET /api/auth/me
```

响应：

```json
{
  "data": {
    "user_id": "u_viewer",
    "username": "viewer",
    "display_name": "普通用户",
    "role": "viewer"
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

### 4.4 可选策略

前端应先读取可选策略，再用用户选中的 `strategy_id` 请求榜单。

```text
GET /api/strategies
```

响应字段：

```json
{
  "data": [
    {
      "strategy_id": "momentum_quality_daily",
      "name": "均衡质量精选",
      "description": "在趋势、质量、估值和波动之间保持均衡，适合作为默认观察池。",
      "model_type": "rule",
      "frequency": "daily",
      "markets": ["cn", "hk"],
      "enabled": true,
      "is_default": true
    }
  ],
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

### 4.5 宏观状态

```text
GET /api/macro-regime
```

响应字段：

```json
{
  "data": {
    "as_of": "2026-05-22T17:40:00+08:00",
    "status": "允许轻仓观察",
    "allow_stock_selection": true,
    "regime": "结构性中性偏谨慎",
    "confidence": 72,
    "summary": "宏观环境没有触发全面回避，但波动中等偏高，应先控制总仓位。",
    "macro_signals": [
      {"label": "流动性", "value": "中性", "tone": "资金面未明显收紧"}
    ],
    "sector_allocation": [
      {"name": "高端制造", "stance": "优先观察", "target": "25%", "reason": "趋势改善"}
    ],
    "position_guidance": {
      "gross": "30% 到 50%",
      "single_stock": "单只不超过 8%",
      "cash_buffer": "保留至少 50% 现金或低风险仓位",
      "rebalance": "宏观状态维持允许观察时，再按日频榜单小步调整。"
    },
    "risk_reminders": [
      "任何个股入选都不能覆盖宏观风险和组合仓位约束。"
    ]
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

如果 `allow_stock_selection=false`，前端不应展示个股 Top N，报告也应优先展示风险提醒和仓位约束。

### 4.6 当前榜单

```text
GET /api/rankings
```

v0.2 约定：接口优先读取 `data/processed/rankings/` 下的本地策略输出；如果对应 `strategy_id / frequency / market / top_n` 文件不存在，再回落到内置样例榜单。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `market` | string | 否 | `cn` 或 `hk`，默认 `cn` |
| `frequency` | string | 否 | `daily` 或 `weekly`，默认 `daily` |
| `top_n` | int | 否 | `20` 或 `50`，默认 `20` |
| `strategy_id` | string | 否 | 策略 ID，默认 `momentum_quality_daily` |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

响应字段：

```json
{
  "data": [
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
      "updated_at": "2026-05-22T18:30:00+08:00"
    }
  ],
  "meta": {
    "request_id": "mock-request",
    "mock": true,
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 2
    }
  }
}
```

### 4.7 股票详情

```text
GET /api/stocks/{symbol}
```

响应字段：

```json
{
  "data": {
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
    "advantages": ["盈利质量稳", "行业地位强"],
    "risks": ["估值不低", "短期波动上升"],
    "recent_performance": {
      "return_5d": 2.1,
      "return_20d": 6.4,
      "max_drawdown_20d": -4.8
    },
    "factor_summary": [
      {
        "factor_name": "momentum_20d",
        "factor_label": "20日趋势",
        "score": 88.0,
        "explanation": "最近 20 日相对市场走势较强。"
      }
    ],
    "price_series": [
      {
        "trade_date": "2026-05-22",
        "close": 1688.0,
        "amount": 5200000000
      }
    ],
    "updated_at": "2026-05-22T18:30:00+08:00"
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

### 4.8 观察名单

```text
GET /api/watchlist
```

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `market` | string | 否 | `cn` 或 `hk` |
| `risk_level` | string | 否 | 风险等级 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

```text
POST /api/watchlist
```

请求：

```json
{
  "symbol": "600519.SH",
  "note": "长期观察行业龙头"
}
```

```text
DELETE /api/watchlist/{symbol}
```

删除成功响应：

```json
{
  "data": {
    "deleted": true,
    "symbol": "600519.SH"
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

观察名单条目字段：

```json
{
  "symbol": "600519.SH",
  "name": "贵州茅台",
  "market": "cn",
  "risk_level": "中",
  "latest_rank": 1,
  "latest_score": 92.5,
  "still_on_ranking": true,
  "note": "长期观察行业龙头",
  "created_at": "2026-05-22T20:00:00+08:00"
}
```

### 4.9 报告列表

```text
GET /api/reports
```

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `frequency` | string | 否 | `daily` 或 `weekly` |
| `market` | string | 否 | `cn` 或 `hk` |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

响应条目字段：

```json
{
  "report_id": "daily-2026-05-22",
  "title": "2026-05-22 AI 候选股日报",
  "frequency": "daily",
  "markets": ["cn", "hk"],
  "summary": "A股和港股候选股整体偏向趋势和质量因子。",
  "published_at": "2026-05-22T19:00:00+08:00"
}
```

### 4.10 报告详情

```text
GET /api/reports/{report_id}
```

响应字段：

```json
{
  "data": {
    "report_id": "daily-2026-05-22",
    "title": "2026-05-22 AI 候选股日报",
    "frequency": "daily",
    "markets": ["cn", "hk"],
    "summary": "A股和港股候选股整体偏向趋势和质量因子。",
    "sections": [
      {
        "heading": "市场概览",
        "content": "今日市场分化，资金更偏好高流动性和盈利质量较稳的公司。"
      }
    ],
    "risk_notice": "本报告仅用于内部研究参考，不构成投资建议。",
    "published_at": "2026-05-22T19:00:00+08:00"
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

### 4.11 任务状态

```text
GET /api/tasks/status
```

权限：`admin`、`researcher`

响应字段：

```json
{
  "data": {
    "as_of": "2026-05-22T20:10:00+08:00",
    "latest_data_update_at": "2026-05-22T17:30:00+08:00",
    "latest_ranking_generated_at": "2026-05-22T18:30:00+08:00",
    "latest_report_generated_at": "2026-05-22T19:00:00+08:00",
    "tasks": [
      {
        "task_id": "data_update_daily",
        "task_name": "日频数据更新",
        "status": "success",
        "started_at": "2026-05-22T16:10:00+08:00",
        "finished_at": "2026-05-22T17:30:00+08:00",
        "message": "mock 数据更新完成"
      }
    ],
    "failed_tasks": []
  },
  "meta": {
    "request_id": "mock-request",
    "mock": true
  }
}
```

## 5. Mock 数据约定

第一阶段 mock 数据需要满足：

1. 覆盖 A股和港股。
2. 覆盖日频和周频榜单。
3. 保留 `strategy_id`，默认 `momentum_quality_daily`，并支持前端切换多个策略。
4. 股票代码沿用内部统一格式，例如 `600519.SH`、`00700.HK`。
5. 所有榜单和详情都必须包含小白解释字段：`reason_summary`、`positive_factors`、`negative_factors`、`risk_level`。
6. 报告统一包含风险提示：`本报告仅用于内部研究参考，不构成投资建议。`
7. mock 数据可放在后端 API service 层，后续替换为评分层、报告层或数据库读取时，不改变前端字段。

## 6. 主控确认事项

### 6.1 已确认

1. 第一轮后端登录继续使用 mock token；进入内部试用前再升级为真实 JWT。
2. 观察名单和报告第一版需要使用 SQLite 持久化；当前 mock API 保持字段和路由不变，后续替换 service 层。
3. 任务状态由 `backend/tasks` 统一对外提供；数据线程负责输出数据更新状态，后端任务层负责聚合展示。
4. 风险等级固定为四档：`低`、`中`、`中高`、`高`。

### 6.2 仍待确认

1. SQLite 表结构和迁移方式是否在后端平台线程下一轮统一补齐。
2. 任务状态是否由 APScheduler 写入本地状态文件，还是由后续数据线程提供状态表后由 `backend/tasks` 聚合。
3. 股票详情中的 `price_series` 最多返回多少条，是否需要单独做行情图接口。
4. 内部试用前真实 JWT、密码加密、管理员建号流程的切换时间点。
