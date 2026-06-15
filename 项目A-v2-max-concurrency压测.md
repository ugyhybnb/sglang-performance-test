# 项目A-v2-max-concurrency压测

更新日期：2026-06-14

## 1. 目标

在固定高到达率 `request-rate=8` 下扫描客户端侧 `max-concurrency`，观察并发上限对 `Qwen3-14B tp=4` 服务吞吐、TTFT、TPOT 和 E2E 长尾的影响。

## 2. 固定条件

| 项 | 值 |
|---|---|
| 模型 | `Qwen3-14B` |
| 服务 | SGLang 单实例 `tp=4` |
| 接口 | `/v1/chat/completions` |
| dataset | `random-ids` |
| prompts | `48` |
| input/output | `512 / 128` tokens |
| request-rate | `8` |
| stream | yes |
| max-concurrency | `1, 2, 4, 8, 16, 32` |

## 3. 结果表

| 场景 | max concurrency | 成功请求 | req/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms | p99 TPOT ms | 实测 concurrency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mc1_rr8_stream | 1 | 48 | 0.73 | 92.82 | 94.33 | 118.22 | 1375.67 | 1394.14 | 10.09 | 10.10 | 1.00 |
| mc2_rr8_stream | 2 | 48 | 1.24 | 159.09 | 103.76 | 127.54 | 1600.26 | 1630.62 | 11.77 | 11.91 | 1.99 |
| mc4_rr8_stream | 4 | 48 | 2.20 | 282.11 | 258.36 | 290.36 | 1793.69 | 1828.78 | 12.47 | 13.43 | 3.95 |
| mc8_rr8_stream | 8 | 48 | 3.49 | 446.75 | 260.32 | 384.02 | 2227.01 | 2274.91 | 15.41 | 17.00 | 7.69 |
| mc16_rr8_stream | 16 | 48 | 5.02 | 642.45 | 452.29 | 990.94 | 3025.28 | 3106.32 | 19.37 | 23.44 | 14.73 |
| mc32_rr8_stream | 32 | 48 | 5.82 | 744.36 | 359.23 | 911.14 | 3872.96 | 4827.55 | 26.59 | 36.75 | 22.02 |

## 4. 产物路径

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| mc1_rr8_stream | `logs/bench_mc1_rr8_stream.log` | `jsonl/mc1_rr8_stream.jsonl` | `metrics/mc1_rr8_stream_metrics.prom` | `metrics/mc1_rr8_stream_gpu.csv` |
| mc2_rr8_stream | `logs/bench_mc2_rr8_stream.log` | `jsonl/mc2_rr8_stream.jsonl` | `metrics/mc2_rr8_stream_metrics.prom` | `metrics/mc2_rr8_stream_gpu.csv` |
| mc4_rr8_stream | `logs/bench_mc4_rr8_stream.log` | `jsonl/mc4_rr8_stream.jsonl` | `metrics/mc4_rr8_stream_metrics.prom` | `metrics/mc4_rr8_stream_gpu.csv` |
| mc8_rr8_stream | `logs/bench_mc8_rr8_stream.log` | `jsonl/mc8_rr8_stream.jsonl` | `metrics/mc8_rr8_stream_metrics.prom` | `metrics/mc8_rr8_stream_gpu.csv` |
| mc16_rr8_stream | `logs/bench_mc16_rr8_stream.log` | `jsonl/mc16_rr8_stream.jsonl` | `metrics/mc16_rr8_stream_metrics.prom` | `metrics/mc16_rr8_stream_gpu.csv` |
| mc32_rr8_stream | `logs/bench_mc32_rr8_stream.log` | `jsonl/mc32_rr8_stream.jsonl` | `metrics/mc32_rr8_stream_metrics.prom` | `metrics/mc32_rr8_stream_gpu.csv` |

## 5. 结论

- `max-concurrency=1/2` 时延稳定，但吞吐被客户端并发限制压住，只达到 `0.73/1.24 req/s`。
- `max-concurrency=4/8` 吞吐提升到 `2.20/3.49 req/s`，E2E p50 保持在 `1.79-2.23s`，是较平衡的并发区间。
- `max-concurrency=16` 吞吐提升到 `5.02 req/s`，但 p99 TTFT 升至 `990.94 ms`，说明首 token 长尾开始明显恶化。
- `max-concurrency=32` 吞吐只比 16 继续增加约 `16%`，但 p99 E2E 升至 `4827.55 ms`，TPOT 也扩大到 `26.59 ms`，边际收益下降。
- 结合 request-rate 阶梯，`rr4`/`mc8` 更适合中压稳定性实验，`rr8`/`mc16+` 可作为高压退化实验。
