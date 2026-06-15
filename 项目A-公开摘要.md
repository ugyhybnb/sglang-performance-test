# 项目A：基于 SGLang 的 4 卡 Qwen3-14B 生产级推理服务压测

## 一句话总结

在 `4 x RTX 4090 24GB` 上使用 SGLang 单实例 `tp=4` 部署 `Qwen3-14B`，围绕 `/v1/chat/completions` 完成容量、长尾时延、prefix cache、混合流量和长时稳定性压测。

## 环境规模

| 项 | 配置 |
|---|---|
| 模型 | `Qwen3-14B` |
| 推理框架 | SGLang |
| GPU | `4 x NVIDIA GeForce RTX 4090 24GB` |
| 服务形态 | 单实例 `tp=4` |
| 主接口 | `/v1/chat/completions` |
| dtype | bf16 |
| KV cache tokens | `298447` |
| context length | `40960` |

## 核心结果

| 场景 | 核心数字 |
|---|---|
| request-rate 基线 | rr4 达到 `3.80 req/s / 486.87 output tok/s`，p99 E2E `4.06s` |
| 高压边界 | rr8 达到 `6.20 req/s / 793.28 output tok/s`，但 p99 E2E 升至 `6.13s` |
| 30 分钟中压稳定性 | `7200/7200` 成功，`3.96 req/s`，p99 TTFT `432.90ms`，p99 E2E `5.42s` |
| 15 分钟高压稳定性 | `7200/7200` 成功，`7.84 req/s`，但 p99 E2E `20.76s` |
| 长 prompt | prompt `8192` 时 p50 TTFT `5710.95ms`，p99 E2E `31.59s` |
| 长输出 | output `256` 时 p50 E2E `3498.09ms`，TPOT 仍约 `13.12ms` |
| shared-prefix | rr4 下 output throughput 从 `466.28` 提升到 `520.66 tok/s` |
| cache 证据 | shared-prefix `cache_hit_token_ratio=0.5818`，随机对照 `0.0023` |

## 关键图表

- `figures/final/throughput_vs_request_rate.png`
- `figures/final/p99_vs_request_rate.png`
- `figures/final/ttft_vs_request_rate.png`
- `figures/final/long_prompt_ttft.png`
- `figures/final/shared_prefix_cache_hit_ratio.png`
- `figures/final/gpu_memory_stability.png`
- `figures/final/queue_running_stability.png`

## 我的工作

- 固定 4 卡 `Qwen3-14B tp=4` 服务启动方案。
- 使用 SGLang OpenAI-compatible `/v1/chat/completions` 接口完成正式压测。
- 为 benchmark 结果建立 JSONL、stdout、metrics、GPU CSV 和图表的可追溯链路。
- 设计 request-rate、max-concurrency、长 prompt、长输出、shared-prefix、混合流量和长时稳定性实验。
- 用 non-stream usage 中的 `cached_tokens` 解释 prefix cache 收益。

## 结论

这套 4 卡 4090 服务可以稳定承载中压在线推理流量；`rr4` 更接近可用于 SLO 分析的稳定区，`rr8` 虽能提高吞吐，但 E2E 长尾和显存余量都进入高风险区。生产使用时应对长 prompt、长输出和混合流量做配额或隔离，否则短请求也会被长请求拖慢。
