# 项目A-v2-request-rate压测

更新日期：2026-06-14

## 1. 目标

建立 `Qwen3-14B + tp=4 + /v1/chat/completions` 的 streaming request-rate 容量基线，观察吞吐、TTFT、TPOT、E2E latency 和资源采样随到达率升高的变化。

## 2. 固定条件

| 项 | 值 |
|---|---|
| 模型 | `Qwen3-14B` |
| 服务 | SGLang 单实例 `tp=4` |
| 接口 | `/v1/chat/completions` |
| backend | `sglang-oai-chat` |
| dataset | `random-ids` |
| prompts | `48` |
| input/output | `512 / 128` tokens |
| stream | yes |
| warmup | `2` |
| cache | 每轮 `--flush-cache` |

统一命令形态：

```bash
/home/dell/Kuiperinfer/projectA_v2/scripts/run_bench_case.sh <scenario> \
  --backend sglang-oai-chat \
  --host 127.0.0.1 \
  --port 30000 \
  --model /home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18 \
  --served-model-name Qwen3-14B \
  --tokenizer /home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18 \
  --dataset-name random-ids \
  --num-prompts 48 \
  --random-input-len 512 \
  --random-output-len 128 \
  --random-range-ratio 1.0 \
  --warmup-requests 2 \
  --disable-tqdm \
  --flush-cache \
  --output-details \
  --request-rate <rr> \
  --output-file /home/dell/Kuiperinfer/projectA_v2/jsonl/<scenario>.jsonl
```

## 3. 结果表

| 场景 | rr | 成功请求 | req/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms | p99 TPOT ms | concurrency | cached tokens | hit ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rr0_5_stream | 0.5 | 48 | 0.54 | 68.69 | 113.32 | 163.66 | 1524.74 | 1768.96 | 11.16 | 13.04 | 0.82 | 0 | 0.0000 |
| rr1_stream | 1.0 | 48 | 1.06 | 135.07 | 109.98 | 183.09 | 1626.41 | 2091.33 | 12.18 | 15.58 | 1.75 | 0 | 0.0000 |
| rr2_stream | 2.0 | 48 | 2.04 | 260.87 | 112.21 | 217.73 | 1881.51 | 2658.36 | 14.63 | 20.08 | 4.03 | 0 | 0.0000 |
| rr4_stream | 4.0 | 48 | 3.80 | 486.87 | 127.57 | 246.26 | 2935.07 | 4064.39 | 21.81 | 31.18 | 11.06 | 0 | 0.0000 |
| rr8_stream | 8.0 | 48 | 6.20 | 793.28 | 218.36 | 563.21 | 4768.74 | 6129.57 | 33.61 | 47.22 | 28.17 | 0 | 0.0000 |

## 4. 产物路径

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| rr0_5_stream | `logs/bench_rr0_5_stream.log` | `jsonl/rr0_5_stream.jsonl` | `metrics/rr0_5_stream_metrics.prom` | `metrics/rr0_5_stream_gpu.csv` |
| rr1_stream | `logs/bench_rr1_stream.log` | `jsonl/rr1_stream.jsonl` | `metrics/rr1_stream_metrics.prom` | `metrics/rr1_stream_gpu.csv` |
| rr2_stream | `logs/bench_rr2_stream.log` | `jsonl/rr2_stream.jsonl` | `metrics/rr2_stream_metrics.prom` | `metrics/rr2_stream_gpu.csv` |
| rr4_stream | `logs/bench_rr4_stream.log` | `jsonl/rr4_stream.jsonl` | `metrics/rr4_stream_metrics.prom` | `metrics/rr4_stream_gpu.csv` |
| rr8_stream | `logs/bench_rr8_stream.log` | `jsonl/rr8_stream.jsonl` | `metrics/rr8_stream_metrics.prom` | `metrics/rr8_stream_gpu.csv` |

## 5. non-stream 对照

non-stream 用于验证 OpenAI usage 和 cache 字段。由于非流式响应只有完整响应完成时间，`bench_serving.py` 中 non-stream 的 TTFT 等于 E2E latency，不用于首 token 体验分析。

| 场景 | rr | 成功请求 | req/s | output tok/s | p50 E2E ms | p99 E2E ms | cached tokens | cache hit ratio | server prompt tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rr1_nonstream | 1.0 | 48 | 1.06 | 135.05 | 1634.50 | 2072.87 | 141 | 0.0053 | 26550 |
| rr4_nonstream | 4.0 | 48 | 3.80 | 486.12 | 2915.53 | 4025.17 | 141 | 0.0053 | 26550 |
| rr8_nonstream | 8.0 | 48 | 6.22 | 796.11 | 4720.15 | 6085.00 | 141 | 0.0053 | 26550 |

non-stream 产物路径：

| 场景 | 日志 | JSONL | metrics | GPU 采样 |
|---|---|---|---|---|
| rr1_nonstream | `logs/bench_rr1_nonstream.log` | `jsonl/rr1_nonstream.jsonl` | `metrics/rr1_nonstream_metrics.prom` | `metrics/rr1_nonstream_gpu.csv` |
| rr4_nonstream | `logs/bench_rr4_nonstream.log` | `jsonl/rr4_nonstream.jsonl` | `metrics/rr4_nonstream_metrics.prom` | `metrics/rr4_nonstream_gpu.csv` |
| rr8_nonstream | `logs/bench_rr8_nonstream.log` | `jsonl/rr8_nonstream.jsonl` | `metrics/rr8_nonstream_metrics.prom` | `metrics/rr8_nonstream_gpu.csv` |

## 6. 结论

- `rr0.5 -> rr2` 区间吞吐基本随到达率增长，p50 TTFT 维持在约 `110 ms`，P99 TTFT 从 `163.66 ms` 增至 `217.73 ms`。
- `rr4` 开始出现明显延迟放大：p50 E2E 达到 `2935.07 ms`，p99 E2E 达到 `4064.39 ms`，mean TPOT 升至 `21.81 ms`。
- `rr8` 的吞吐继续上升到 `6.20 req/s / 793.28 output tok/s`，但 p99 TTFT 升至 `563.21 ms`，p99 E2E 升至 `6129.57 ms`，说明服务已经进入高压退化区。
- 当前随机负载每轮 flush cache，streaming usage 不提供 cache 统计，因此 streaming cached tokens 为 `0` 是预期现象；non-stream usage 显示随机负载 `cache_hit_token_ratio=0.0053`，可视为接近无 cache 收益。
- 同压力点下 non-stream E2E 与 stream E2E 接近，说明两种模式对服务负载的影响在本实验中差异不大；TTFT/ITL/TPOT 仍以 streaming 结果为准。
- 后续 max-concurrency 与稳定性实验建议以 `rr4` 作为中高压力点，以 `rr8` 作为高压退化点。
