# 项目A-v2-长时稳定性专项

更新日期：2026-06-14

## 1. 目标

验证 `Qwen3-14B tp=4` 在线服务在持续流量下的稳定性，观察错误率、timeout、显存漂移、queue、running requests、时延漂移和高压退化方式。

## 2. 实验设置

| 场景 | request-rate | prompts | input/output | 目标时长 | 实际时长 | stream |
|---|---:|---:|---:|---:|---:|---|
| stability_mid_rr4_30m | 4 | 7200 | 512 / 128 | 30 min | 1818.51 s | yes |
| stability_high_rr8_15m | 8 | 7200 | 512 / 128 | 15 min | 918.11 s | yes |

## 3. 结果表

| 场景 | 成功请求 | req/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms | p99 TPOT ms | concurrency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stability_mid_rr4_30m | 7200 | 3.96 | 506.79 | 141.80 | 432.90 | 2981.47 | 5422.32 | 23.19 | 40.98 | 12.32 |
| stability_high_rr8_15m | 7200 | 7.84 | 1003.81 | 238.91 | 753.89 | 13082.93 | 20761.55 | 96.91 | 161.36 | 98.69 |

## 4. 资源与队列

| 场景 | GPU | 显存 min MiB | 显存 max MiB | 平均 GPU util % | 最高温度 C |
|---|---:|---:|---:|---:|---:|
| mid rr4 | 0 | 21357 | 21559 | 96.91 | 87 |
| mid rr4 | 1 | 21361 | 21561 | 97.42 | 92 |
| mid rr4 | 2 | 21361 | 21561 | 97.01 | 85 |
| mid rr4 | 3 | 21361 | 21561 | 97.48 | 92 |
| high rr8 | 0 | 21359 | 23747 | 93.95 | 88 |
| high rr8 | 1 | 21361 | 23747 | 95.49 | 92 |
| high rr8 | 2 | 21361 | 23747 | 93.35 | 86 |
| high rr8 | 3 | 21361 | 23747 | 95.55 | 92 |

Queue 观测：

| 场景 | max queue | 观察 |
|---|---:|---|
| stability_mid_rr4_30m | 0 | queue 未堆积，running requests 通常在个位数到十几之间波动 |
| stability_high_rr8_15m | 2 | queue 基本不堆积，但 running requests 可升至百级，服务通过更高在飞请求吸收高压 |

## 5. 产物路径

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| stability_mid_rr4_30m | `logs/bench_stability_mid_rr4_30m.log` | `jsonl/stability_mid_rr4_30m.jsonl` | `metrics/stability_mid_rr4_30m_metrics.prom` | `metrics/stability_mid_rr4_30m_gpu.csv` |
| stability_high_rr8_15m | `logs/bench_stability_high_rr8_15m.log` | `jsonl/stability_high_rr8_15m.jsonl` | `metrics/stability_high_rr8_15m_metrics.prom` | `metrics/stability_high_rr8_15m_gpu.csv` |

## 6. 结论

- 中压 rr4 持续 30 分钟完成 `7200/7200` 请求，没有错误或 timeout；p99 TTFT `432.90 ms`，p99 E2E `5422.32 ms`，显存只从约 `21.36GB` 到 `21.56GB`，未见失控式漂移。
- 高压 rr8 持续约 15 分钟完成 `7200/7200` 请求，没有失败；吞吐达到 `7.84 req/s / 1003.81 output tok/s`，但 p50 E2E `13.08s`、p99 E2E `20.76s`，明显不适合交互式 SLO。
- 高压下显存最高约 `23.75GB`，接近 4090 24GB 上限；虽然未 OOM，但可用余量很小，应视为高风险运行区。
- 两档实验的 queue 都没有持续堆积，中压 max queue 为 `0`，高压 max queue 为 `2`；退化主要体现为 running requests 增多、TPOT/ITL 拉长和 E2E 长尾扩大。
- 对生产配置，rr4 可作为中压稳定运行参考点；rr8 可作为容量上界/退化边界，不建议作为稳定 SLO 承诺点。
