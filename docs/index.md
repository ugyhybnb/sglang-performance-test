# sglang-performance-test-v2

## 基于 SGLang 的 4 卡 Qwen3-14B 推理服务压测


我在 `4 x RTX 4090 24GB` 上使用 SGLang 单实例 `tp=4` 部署 `Qwen3-14B`，围绕 `/v1/chat/completions` 做了容量边界、长尾时延、prefix cache、混合流量和长时稳定性分析，并将 benchmark、metrics、GPU 采样、图表和结论整理成一个公开可浏览的项目页。

## 我想解决什么问题

从服务化视角对大模型压测

这个项目重点回答的是：

- 4 卡 14B 服务能否稳定运行
- 容量边界和退化边界在哪里
- 长 prompt、长输出和混合流量分别伤到哪些指标
- prefix cache 的收益体现
- 中压稳定区和高压退化区如何区分

## 一眼看结论

- `rr4` 是更适合做稳定区分析的中压点
- `rr8` 虽然吞吐更高，但已经进入长尾和显存风险明显抬升的退化区
- shared-prefix 效果由 `cached_tokens` 和 `cache_hit_token_ratio` 支撑
- 长 prompt 主要伤 `TTFT`，长输出主要伤 `E2E latency`

## 核心数字

| 场景 | 结果 |
|---|---|
| rr4 基线 | `3.80 req/s / 486.87 output tok/s` |
| rr8 基线 | `6.20 req/s / 793.28 output tok/s` |
| 30 分钟稳定性 | `7200/7200` 成功，p99 TTFT `432.90ms` |
| 15 分钟高压 | `7200/7200` 成功，但 p99 E2E `20.76s` |
| shared-prefix | cache hit token ratio `0.5818` |
| random 对照 | cache hit token ratio `0.0023` |

## 图表

### 容量与时延

![Throughput vs Request Rate](assets/throughput_vs_request_rate.png)

![P99 vs Request Rate](assets/p99_vs_request_rate.png)

![TTFT vs Request Rate](assets/ttft_vs_request_rate.png)

### 长 prompt / 长输出

![Long Prompt TTFT](assets/long_prompt_ttft.png)

![Long Output E2E and TPOT](assets/long_output_e2e_tpot.png)

### Prefix Cache

![Shared Prefix Throughput](assets/shared_prefix_throughput.png)

![Shared Prefix Cache Hit Ratio](assets/shared_prefix_cache_hit_ratio.png)

### 稳定性

![GPU Memory Stability](assets/gpu_memory_stability.png)

![Queue Running Stability](assets/queue_running_stability.png)




