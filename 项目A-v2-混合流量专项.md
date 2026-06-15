# 项目A-v2-混合流量专项

更新日期：2026-06-14

## 1. 目标

构造更接近线上服务的混合流量，观察短问答、长 prompt、shared-prefix 和长输出请求共同进入服务时，哪类请求最容易成为长尾来源。

## 2. 实现方式

新增脚本：

- `scripts/run_mixed_traffic.py`
- `scripts/run_mixed_case.sh`

该脚本不修改 SGLang 调度逻辑，只通过 `/v1/chat/completions` 发送 streaming 请求，并记录逐请求 JSONL。

混合流量组成：

| 类型 | 数量 | prompt | output |
|---|---:|---:|---:|
| short_qa | 12 | 256 | 64 |
| long_prompt | 8 | 4096 | 64 |
| long_output | 8 | 512 | 256 |
| shared_prefix | 16 | system 1024 + question 128 | 128 |

运行条件：

| 项 | 值 |
|---|---|
| request-rate | `4` |
| total requests | `44` |
| successful requests | `44` |
| request throughput | `2.69 req/s` |
| stream | yes |

命令：

```bash
/home/dell/Kuiperinfer/projectA_v2/scripts/run_mixed_case.sh mixed_rr4 \
  --tokenizer /home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18 \
  --request-rate 4 \
  --output-file /home/dell/Kuiperinfer/projectA_v2/jsonl/mixed_rr4.jsonl
```

## 3. 分类型结果

| 类型 | 请求数 | 成功 | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean ITL ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| short_qa | 12 | 12 | 96.26 | 734.77 | 1887.62 | 3265.71 | 25.62 |
| long_prompt | 8 | 8 | 746.21 | 1029.53 | 2042.72 | 4102.91 | 26.31 |
| long_output | 8 | 8 | 359.06 | 893.12 | 6651.99 | 8772.33 | 23.74 |
| shared_prefix | 16 | 16 | 310.66 | 789.26 | 3982.12 | 5850.65 | 29.02 |

## 4. 产物路径

| 内容 | 路径 |
|---|---|
| stdout 日志 | `logs/mixed_mixed_rr4.log` |
| JSONL | `jsonl/mixed_rr4.jsonl` |
| metrics | `metrics/mixed_rr4_metrics.prom` |
| GPU 采样 | `metrics/mixed_rr4_gpu.csv` |
| 混合脚本 | `scripts/run_mixed_traffic.py` |
| 采样 wrapper | `scripts/run_mixed_case.sh` |

## 5. 结论

- `long_output` 是混合流量中的最大 E2E 长尾来源，p50 E2E `6651.99 ms`，p99 E2E `8772.33 ms`。
- `long_prompt` 是最明显的 TTFT 压力来源，p50 TTFT `746.21 ms`，p99 TTFT `1029.53 ms`。
- `short_qa` 本身很短，但在混合流量中 p50 E2E 仍被拖到 `1887.62 ms`，说明短请求会受到同 batch 中长请求和整体负载影响。
- `shared_prefix` 在混合流量中仍能运行成功，但收益被长输出和长 prompt 混合负载稀释；其 p50 E2E `3982.12 ms` 高于 shared-prefix 单项 rr4 stream 的 `2544.20 ms`。
- 混合 workload 下，服务退化不是单一指标变坏：长 prompt 先伤 TTFT，长输出主要拉高 E2E，短请求也会被共同调度环境拖慢。
