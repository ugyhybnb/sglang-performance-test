# 项目A-v2

## 基于 SGLang 的 4 卡 Qwen3-14B 生产级推理服务压测

这是一个面向推理 infra 岗位的作品集项目。

我在 `4 x RTX 4090 24GB` 上使用 SGLang 单实例 `tp=4` 部署 `Qwen3-14B`，围绕 `/v1/chat/completions` 做了容量边界、长尾时延、prefix cache、混合流量和长时稳定性分析，并将 benchmark、metrics、GPU 采样、图表和结论整理成一个公开可浏览的项目页。

## 我想解决什么问题

很多“大模型压测项目”只有几条 benchmark 输出，缺少服务化视角。

这个项目重点回答的是：

- 4 卡 14B 服务能否稳定运行
- 容量边界和退化边界在哪里
- 长 prompt、长输出和混合流量分别伤到哪些指标
- prefix cache 的收益能不能被真实数据证明
- 中压稳定区和高压退化区如何区分

## 一眼看结论

- `rr4` 是更适合做稳定区分析的中压点
- `rr8` 虽然吞吐更高，但已经进入长尾和显存风险明显抬升的退化区
- shared-prefix 的收益不是“感觉变快了”，而是有 `cached_tokens` 和 `cache_hit_token_ratio` 证据支撑
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

## 为什么这些结果可信

这个项目不是只放结论图。

背后保留了完整证据链：

- 服务基线文档
- benchmark JSONL
- Prometheus metrics 采样
- GPU CSV 采样
- 绘图脚本
- 各专项技术报告

也就是说，这个页面是结果入口，不是唯一材料。

## 项目结构

- 仓库首页：查看仓库根目录 `README.md`
- 完整技术报告：查看仓库根目录 `项目A-v2-最终结果文档.md`
- 公开摘要：查看仓库根目录 `项目A-公开摘要.md`
- 复现说明：查看仓库根目录 `项目A-复现说明.md`
- 简历描述：查看仓库根目录 `项目A-v2-简历描述.md`
- 产物清单：查看仓库根目录 `ARTIFACTS.md`

## 发布建议

这个目录可以直接作为 GitHub Pages 的 `docs/` 目录使用。

推荐在 GitHub 仓库中：

1. 把仓库主页入口设为根目录 `README.md`
2. 把 GitHub Pages 源设置为 `main` 分支下的 `/docs`
3. 用这个页面作为项目展示页
