# 项目A-v2-长prompt专项

更新日期：2026-06-14

## 1. 目标

观察 `Qwen3-14B tp=4` 在 prefill 主导场景下的服务表现，重点分析 prompt 变长后 TTFT、E2E latency、吞吐和排队风险的变化。

## 2. 固定条件

| 项 | 值 |
|---|---|
| dataset | `random-ids` |
| prompts | `24` |
| prompt length | `512, 2048, 4096, 8192` |
| output length | `64` |
| request-rate | `1` |
| stream | yes |
| cache | 每轮 `--flush-cache` |

## 3. 结果表

| 场景 | input tokens | 成功请求 | req/s | input tok/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms | p99 TPOT ms | concurrency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| long_prompt_512_stream | 512 | 24 | 1.38 | 705.63 | 88.20 | 105.67 | 152.26 | 888.24 | 1048.54 | 12.05 | 14.76 | 1.20 |
| long_prompt_2048_stream | 2048 | 24 | 1.34 | 2734.74 | 85.46 | 382.19 | 639.57 | 1643.72 | 2358.48 | 18.86 | 31.91 | 2.16 |
| long_prompt_4096_stream | 4096 | 24 | 1.23 | 5042.22 | 78.78 | 1198.41 | 1937.58 | 6269.05 | 12551.00 | 82.81 | 186.50 | 7.92 |
| long_prompt_8192_stream | 8192 | 24 | 0.76 | 6208.94 | 48.51 | 5710.95 | 13209.64 | 21130.01 | 31587.89 | 248.38 | 471.65 | 16.68 |

## 4. 产物路径

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| long_prompt_512_stream | `logs/bench_long_prompt_512_stream.log` | `jsonl/long_prompt_512_stream.jsonl` | `metrics/long_prompt_512_stream_metrics.prom` | `metrics/long_prompt_512_stream_gpu.csv` |
| long_prompt_2048_stream | `logs/bench_long_prompt_2048_stream.log` | `jsonl/long_prompt_2048_stream.jsonl` | `metrics/long_prompt_2048_stream_metrics.prom` | `metrics/long_prompt_2048_stream_gpu.csv` |
| long_prompt_4096_stream | `logs/bench_long_prompt_4096_stream.log` | `jsonl/long_prompt_4096_stream.jsonl` | `metrics/long_prompt_4096_stream_metrics.prom` | `metrics/long_prompt_4096_stream_gpu.csv` |
| long_prompt_8192_stream | `logs/bench_long_prompt_8192_stream.log` | `jsonl/long_prompt_8192_stream.jsonl` | `metrics/long_prompt_8192_stream_metrics.prom` | `metrics/long_prompt_8192_stream_gpu.csv` |

## 5. 结论

- `512 -> 2048` 时，p50 TTFT 从 `105.67 ms` 增至 `382.19 ms`，E2E p50 从 `888.24 ms` 增至 `1643.72 ms`，prefill 成本开始显性化。
- `4096` 是明显拐点：p50 TTFT 达到 `1198.41 ms`，p99 E2E 达到 `12551.00 ms`，说明较长 prompt 下请求堆叠会快速放大长尾。
- `8192` 已进入强 prefill 压力区：p50 TTFT `5710.95 ms`，p99 TTFT `13209.64 ms`，p99 E2E `31587.89 ms`，吞吐降至 `0.76 req/s`。
- prompt 增长后，吞吐下降不是线性的；当 prefill 时间超过到达间隔后，实测 concurrency 从 `1.20` 增至 `16.68`，排队和批处理叠加导致长尾快速恶化。
- 对该服务，`2048` 以内更接近可控 RAG 输入区；`4096+` 需要降低 request-rate、限制并发或拆分 workload，否则 P99 很难维持交互式 SLO。
