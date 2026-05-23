# 数据线程 Hypatia 完成汇报

## 1. 线程信息

| 项目 | 内容 |
| --- | --- |
| 线程名称 | 数据线程 |
| 代理昵称 | Hypatia |
| 负责范围 | 免费数据源、A股/港股数据管道、数据清洗、字段标准化、数据质量检查 |
| 当前状态 | 第一轮已复核并补齐 |

## 2. 已完成内容

1. 免费数据源评估：第一版以 AkShare 作为原型数据入口，后续可替换或扩展到付费源。
2. 数据源封装：通过 `backend/data_sources/` 隔离 AkShare 函数名和原始中文字段。
3. 股票池快照：支持 A股、港股、港股通快照入口。
4. 个股日线：支持 A股、港股日线拉取，保留复权参数。
5. 交易日历：补齐 A股交易日历标准化和本地落盘流程。
6. 指数行情：补齐 A股指数日线标准化和本地落盘流程。
7. 估值快照：补齐从股票快照中提取 PE、PB、市值、成交额等字段的流程。
8. 数据标准化：统一股票代码、日期、币种、成交量单位、来源字段。
9. 数据质量检查：覆盖必填字段、重复主键、OHLC 异常、零成交、复权混用、交易日滞后、估值缺字段等检查。
10. 股票池过滤：补齐第一版结构化过滤器，可输出排除原因。
11. 本地存储：原始数据进入 `data/raw/`，标准化数据进入 `data/processed/`，当前使用 JSONL fallback。
12. 数据字典：补齐 `securities`、`trade_calendar`、`daily_bars`、`index_bars`、`valuation_snapshots`、`universe_filter_decisions`。

## 3. 主要产出文件

| 文件 | 说明 |
| --- | --- |
| `docs/数据源评估.md` | 免费数据源评估、限制、当前覆盖面 |
| `docs/数据字典.md` | 数据字段、字段映射、质量规则 |
| `backend/data_sources/base.py` | Provider 中立协议和请求对象 |
| `backend/data_sources/akshare_provider.py` | AkShare 数据源封装 |
| `backend/data_pipeline/schemas.py` | 标准化数据结构 |
| `backend/data_pipeline/normalizers.py` | AkShare 原始字段到内部字段的转换 |
| `backend/data_pipeline/quality.py` | 数据质量检查 |
| `backend/data_pipeline/storage.py` | 本地 JSONL/CSV 存储 |
| `backend/data_pipeline/runner.py` | 数据更新编排 |
| `backend/data_pipeline/filters.py` | 股票池过滤器 |
| `data/README.md` | 本地数据目录约定 |
| `tests/test_data_pipeline.py` | 无外部行情依赖的数据管道 smoke test |
| `scripts/run_live_data_sample.py` | 真实外部数据小样本拉取脚本 |

## 4. 对其他线程的影响

1. 策略框架线程、因子线程、回测线程应读取 `data/processed/` 下的标准化字段，不直接读取 `data/raw/` 或 AkShare 原始字段。
2. 后端任务状态可以使用 `PipelineResult.issues` 汇总数据更新质量状态。
3. 因子和策略可以依赖 `volume` 已统一为股数，但需要关注 `source_volume_unit` 追溯原始单位。
4. `valuation_snapshots` 只能作为估值快照和过滤辅助，暂不等同披露日严格处理后的财务因子。

## 5. 尚未完成或待确认

1. 港股独立交易日历仍需确认稳定免费源；MVP 可暂用实际行情日期反推。
2. 港股指数历史行情源仍未固化；MVP 先补 A股指数日线。
3. 股票池过滤阈值尚未固化，例如最低成交额、最低价格、市值下限。
4. 财报字段进入模型或回测前，需要先确认披露日可见性规则。
5. 当前机器 `python3` 为 3.9.6，项目 `pyproject.toml` 要求 Python 3.11+；运行真实 AkShare 前需统一环境并安装依赖。

## 6. 验证结果

已完成数据线程 Python 语法编译、无 AkShare 依赖的本地管道 smoke test，以及真实外部数据小样本拉取。

真实拉取已落盘：

- `data/processed/daily_bars/market=cn/symbol=000001_SZ/adjust=none/part.jsonl`
- `data/processed/daily_bars/market=hk/symbol=00700_HK/adjust=none/part.jsonl`
- `data/processed/trade_calendar/market=cn/part.jsonl`
- `data/processed/index_bars/market=cn/symbol=000300_CN/part.jsonl`
- `data/processed/valuation_snapshots/market=cn/part.jsonl`
- `data/processed/valuation_snapshots/market=hk/part.jsonl`
