# 项目A-v2-shared-prefix专项

更新日期：2026-06-14

## 1. 目标

验证 `Qwen3-14B tp=4` 正式服务中 prefix cache 对真实 cache 友好 workload 的收益，并用随机长度相近负载作对照。

## 2. 固定条件

| 项 | random 对照 | shared-prefix |
|---|---|---|
| dataset | `random-ids` | `generated-shared-prefix` |
| prompts | `32` | `8 groups x 4 prompts` |
| 输入长度 | `1152` | system `1024` + question `128` |
| 输出长度 | `128` | `128` |
| request-rate | `2, 4` | `2, 4` |
| stream | yes + rr4 non-stream | yes + rr4 non-stream |
| cache | 每轮开始前 `--flush-cache` | 每轮开始前 `--flush-cache`，同轮内复用 shared prefix |

## 3. stream 结果

| 场景 | rr | workload | 成功请求 | req/s | input tok/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random1152_rr2_stream | 2 | random-ids | 32 | 2.23 | 2565.88 | 285.10 | 223.61 | 437.09 | 3314.61 | 4646.66 | 23.24 |
| gsp1024_rr2_stream | 2 | generated-shared-prefix | 32 | 2.29 | 2775.38 | 293.66 | 112.30 | 517.05 | 1830.45 | 3423.07 | 15.57 |
| random1152_rr4_stream | 4 | random-ids | 32 | 3.64 | 4196.56 | 466.28 | 556.07 | 1024.48 | 5687.26 | 7928.80 | 39.33 |
| gsp1024_rr4_stream | 4 | generated-shared-prefix | 32 | 4.07 | 4920.72 | 520.66 | 130.00 | 836.31 | 2544.20 | 4406.50 | 20.15 |

## 4. non-stream cache 证据

non-stream 的 TTFT 等于 E2E，不用于首 token 指标；这里主要使用 OpenAI-compatible usage 里的 `prompt_tokens_details.cached_tokens` 聚合字段。

| 场景 | rr | workload | 成功请求 | req/s | p50 E2E ms | p99 E2E ms | cached tokens | cache hit ratio |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| random1152_rr4_nonstream | 4 | random-ids | 32 | 3.64 | 5715.91 | 7999.28 | 90 | 0.0023 |
| gsp1024_rr4_nonstream | 4 | generated-shared-prefix | 32 | 4.08 | 2501.82 | 4342.86 | 22671 | 0.5818 |

## 5. 产物路径

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| random1152_rr2_stream | `logs/bench_random1152_rr2_stream.log` | `jsonl/random1152_rr2_stream.jsonl` | `metrics/random1152_rr2_stream_metrics.prom` | `metrics/random1152_rr2_stream_gpu.csv` |
| gsp1024_rr2_stream | `logs/bench_gsp1024_rr2_stream.log` | `jsonl/gsp1024_rr2_stream.jsonl` | `metrics/gsp1024_rr2_stream_metrics.prom` | `metrics/gsp1024_rr2_stream_gpu.csv` |
| random1152_rr4_stream | `logs/bench_random1152_rr4_stream.log` | `jsonl/random1152_rr4_stream.jsonl` | `metrics/random1152_rr4_stream_metrics.prom` | `metrics/random1152_rr4_stream_gpu.csv` |
| gsp1024_rr4_stream | `logs/bench_gsp1024_rr4_stream.log` | `jsonl/gsp1024_rr4_stream.jsonl` | `metrics/gsp1024_rr4_stream_metrics.prom` | `metrics/gsp1024_rr4_stream_gpu.csv` |
| random1152_rr4_nonstream | `logs/bench_random1152_rr4_nonstream.log` | `jsonl/random1152_rr4_nonstream.jsonl` | `metrics/random1152_rr4_nonstream_metrics.prom` | `metrics/random1152_rr4_nonstream_gpu.csv` |
| gsp1024_rr4_nonstream | `logs/bench_gsp1024_rr4_nonstream.log` | `jsonl/gsp1024_rr4_nonstream.jsonl` | `metrics/gsp1024_rr4_nonstream_metrics.prom` | `metrics/gsp1024_rr4_nonstream_gpu.csv` |

## 6. 结论

- rr2 下，GSP 的 p50 TTFT 从随机对照的 `223.61 ms` 降至 `112.30 ms`，p50 E2E 从 `3314.61 ms` 降至 `1830.45 ms`。
- rr4 下，GSP 的吞吐从 `3.64 req/s / 466.28 tok/s` 提升至 `4.07 req/s / 520.66 tok/s`，同时 p50 E2E 从 `5687.26 ms` 降至 `2544.20 ms`。
- rr4 non-stream usage 中，随机对照 `cache_hit_token_ratio=0.0023`，GSP 达到 `0.5818`，`cached_tokens=22671`，说明收益来自共享 prefix 的缓存复用。
- streaming 响应当前不稳定返回 final usage，因此 stream 结果中的 cached tokens 为 `0` 不代表没有 cache；cache 证据以 non-stream usage 和服务日志 `#cached-token` 为准。
- 在更高压力 rr4 下，shared-prefix 收益仍然成立，但 p99 TTFT 仍有 `836.31 ms`，说明 cache 能减少 prefill 重复计算，但不能完全消除高压下的调度和 decode 长尾。
