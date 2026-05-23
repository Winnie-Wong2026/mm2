# processed

保存数据线程标准化后的内部字段。因子、策略、回测和 API 后续应读取这里的稳定字段，而不是直接读取 `data/raw/`。

v0.2 已补充本地策略样本输出：

```text
data/processed/factors/strategy_id=momentum_quality_daily/frequency=daily/part.jsonl
data/processed/strategy_signals/strategy_id=momentum_quality_daily/frequency=daily/part.jsonl
data/processed/rankings/strategy_id=momentum_quality_daily/frequency=daily/market=cn/top_n=20/part.jsonl
data/processed/rankings/strategy_id=momentum_quality_daily/frequency=daily/market=hk/top_n=20/part.jsonl
```

重新生成样本：

```text
.venv/bin/python scripts/run_strategy_sample.py
```
