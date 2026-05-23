# data 目录说明

本目录只存放本地运行产生的数据样例、缓存和说明文件，不把免费数据源的临时字段直接暴露给策略、因子、评分或前端。

## 目录约定

| 目录 | 用途 |
| --- | --- |
| `raw/` | AkShare 等数据源原始返回，保留原始字段和 `source_function` |
| `processed/` | 数据线程标准化后的内部字段，例如 `daily_bars`、`securities`、`trade_calendar`、`index_bars`、`valuation_snapshots` |

## 第一版落地格式

当前环境未安装 `pandas`、`pyarrow`、`duckdb`，因此代码骨架默认使用 JSONL 作为无依赖 fallback。主控确认依赖后，可新增 Parquet/DuckDB 写入器，但不要改变上层标准字段。

示例分区：

```text
data/raw/daily_bars/market=cn/symbol=000001_SZ/adjust=none/part.jsonl
data/processed/daily_bars/market=cn/symbol=000001_SZ/adjust=none/part.jsonl
data/processed/securities/market=hk/part.jsonl
data/processed/trade_calendar/market=cn/part.jsonl
data/processed/index_bars/market=cn/symbol=000300_CN/part.jsonl
data/processed/valuation_snapshots/market=cn/part.jsonl
```

## 真实数据小样本

项目环境已使用 `uv` 创建 `.venv`。重新拉取核心真实数据样本：

```text
python3 -m uv run python scripts/run_live_data_sample.py
```

如需额外拉全市场 A股/港股快照：

```text
python3 -m uv run python scripts/run_live_data_sample.py --include-snapshots
```

全市场快照接口较慢，且免费源偶发返回空响应；行情、交易日历和指数样本默认不依赖该步骤。
