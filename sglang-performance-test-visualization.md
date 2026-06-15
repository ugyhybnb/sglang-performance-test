# sglang-performance-test visualization notes

更新日期：2026-06-14

## 1. 生成命令

```bash
/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python \
  /home/dell/Kuiperinfer/projectA_v2/scripts/plot_projectA_v2.py \
  > /home/dell/Kuiperinfer/projectA_v2/logs/plot_projectA_v2.log 2>&1
```

绘图脚本：

`scripts/plot_projectA_v2.py`

执行日志：

`logs/plot_projectA_v2.log`

## 2. 图表清单

| 图表 | 路径 | 数据来源 | 用途 |
|---|---|---|---|
| 吞吐 vs request-rate | `figures/final/throughput_vs_request_rate.png` | `jsonl/rr*_stream.jsonl` | 展示吞吐随到达率增长和平台区 |
| P99 latency vs request-rate | `figures/final/p99_vs_request_rate.png` | `jsonl/rr*_stream.jsonl` | 展示长尾时延拐点 |
| TTFT vs request-rate | `figures/final/ttft_vs_request_rate.png` | `jsonl/rr*_stream.jsonl` | 展示首 token 长尾变化 |
| 长 prompt TTFT | `figures/final/long_prompt_ttft.png` | `jsonl/long_prompt_*_stream.jsonl` | 展示 prefill 主导场景退化 |
| 长输出 E2E/TPOT | `figures/final/long_output_e2e_tpot.png` | `jsonl/long_output_*_stream.jsonl` | 展示 decode 主导场景退化 |
| shared-prefix 吞吐对比 | `figures/final/shared_prefix_throughput.png` | `jsonl/random1152_rr4_stream.jsonl`, `jsonl/gsp1024_rr4_stream.jsonl` | 展示 cache 友好 workload 吞吐收益 |
| shared-prefix cache 命中 | `figures/final/shared_prefix_cache_hit_ratio.png` | `jsonl/random1152_rr4_nonstream.jsonl`, `jsonl/gsp1024_rr4_nonstream.jsonl` | 展示 cached_tokens 证据 |
| 稳定性显存时序 | `figures/final/gpu_memory_stability.png` | `metrics/stability_*_gpu.csv` | 展示显存稳定性和高压余量 |
| 稳定性 GPU 利用率时序 | `figures/final/gpu_utilization_stability.png` | `metrics/stability_*_gpu.csv` | 展示持续压测资源利用 |
| running/queue 时序 | `figures/final/queue_running_stability.png` | `metrics/stability_*_metrics.prom` | 展示高压退化时 running/queue 行为 |
| 稳定性 P99 E2E | `figures/final/stability_p99_e2e.png` | `jsonl/stability_*jsonl` | 对比中压和高压 SLO 风险 |

## 3. 汇总 CSV

| 文件 | 来源 |
|---|---|
| `figures/raw/request_rate_summary.csv` | request-rate JSONL 汇总 |
| `figures/raw/long_prompt_summary.csv` | 长 prompt JSONL 汇总 |
| `figures/raw/long_output_summary.csv` | 长输出 JSONL 汇总 |
| `figures/raw/shared_prefix_summary.csv` | shared-prefix stream/non-stream 汇总 |
| `figures/raw/stability_summary.csv` | 长时稳定性 JSONL 汇总 |

## 4. 说明

- `figures/raw` 和 `figures/final` 中 PNG 内容一致，raw 目录额外保存中间 CSV。
- 图表数字来自 JSONL、metrics 和 GPU CSV，不使用手工录入截图。
- shared-prefix 的 cache 图使用 non-stream usage 字段，因为当前 streaming final chunk 不稳定返回 usage。
