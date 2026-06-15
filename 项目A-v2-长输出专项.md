# 项目A-v2-长输出专项

更新日期：2026-06-14

## 1. 目标

观察 `Qwen3-14B tp=4` 在 decode 主导场景下的表现，重点分析输出长度增加后 TPOT、ITL、E2E latency 和吞吐变化。

## 2. 固定条件

| 项 | 值 |
|---|---|
| dataset | `random-ids` |
| prompts | `24` |
| prompt length | `512` |
| output length | `64, 128, 256` |
| request-rate | `1` |
| stream | yes |
| cache | 每轮 `--flush-cache` |

## 3. 结果表

| 场景 | output tokens | 成功请求 | req/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms | p99 TPOT ms | p99 ITL ms | concurrency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| long_output_64_stream | 64 | 24 | 1.38 | 88.18 | 107.10 | 153.75 | 888.50 | 1058.92 | 12.13 | 14.90 | 56.47 | 1.21 |
| long_output_128_stream | 128 | 24 | 1.32 | 168.97 | 110.34 | 151.15 | 1679.18 | 1906.19 | 12.31 | 14.10 | 53.93 | 2.22 |
| long_output_256_stream | 256 | 24 | 1.21 | 310.92 | 110.89 | 153.68 | 3498.09 | 3773.17 | 13.12 | 14.35 | 54.36 | 4.20 |

## 4. 产物路径

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| long_output_64_stream | `logs/bench_long_output_64_stream.log` | `jsonl/long_output_64_stream.jsonl` | `metrics/long_output_64_stream_metrics.prom` | `metrics/long_output_64_stream_gpu.csv` |
| long_output_128_stream | `logs/bench_long_output_128_stream.log` | `jsonl/long_output_128_stream.jsonl` | `metrics/long_output_128_stream_metrics.prom` | `metrics/long_output_128_stream_gpu.csv` |
| long_output_256_stream | `logs/bench_long_output_256_stream.log` | `jsonl/long_output_256_stream.jsonl` | `metrics/long_output_256_stream_metrics.prom` | `metrics/long_output_256_stream_gpu.csv` |

## 5. 结论

- 输出长度从 `64 -> 256` 时，p50 TTFT 基本稳定在 `107-111 ms`，说明首 token 主要由 prefill 和调度决定，输出长度本身不显著影响 TTFT。
- E2E latency 随输出长度显著增长：p50 E2E 从 `888.50 ms` 增至 `3498.09 ms`，p99 E2E 从 `1058.92 ms` 增至 `3773.17 ms`。
- mean TPOT 只从 `12.13 ms` 小幅增至 `13.12 ms`，p99 TPOT 维持在约 `14-15 ms`，说明在 `request-rate=1` 下 decode 阶段仍较稳定。
- 实测 concurrency 从 `1.21` 增至 `4.20`，说明长输出会增加请求驻留时间，即使 TTFT 稳定，也会提高系统内在飞请求数。
- 相比长 prompt 专项，长输出主要拉长 E2E，而不是显著放大 TTFT；对交互式服务，长输出更适合通过 `max_completion_tokens`、流式返回和队列隔离控制。
