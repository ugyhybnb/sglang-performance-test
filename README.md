# 项目A-v2：基于 SGLang 的 4 卡 Qwen3-14B 生产级推理服务压测

这个仓库展示一个面向推理 infra 岗位的名片项目：

在 `4 x RTX 4090 24GB` 上使用 SGLang 单实例 `tp=4` 部署 `Qwen3-14B`，围绕 `/v1/chat/completions` 完成容量边界、长尾时延、prefix cache、混合流量和长时稳定性压测，并沉淀成可复现、可展示、可讲述的项目材料。

## 为什么这个项目值得看

- 它不是“跑通服务”的练手项目，而是完整的推理服务压测闭环。
- 它不只给 benchmark 数字，还给出 metrics、GPU 采样、图表和结论之间的证据链。
- 它覆盖真实线上更关心的问题：容量边界、长尾时延、长 prompt、长输出、cache 友好流量和稳定性。

## 项目亮点

- 服务形态：`Qwen3-14B`、单实例 `tp=4`、`bf16`
- 机器规格：`4 x NVIDIA GeForce RTX 4090 24GB`
- 正式接口：`/v1/chat/completions`
- 压测覆盖：request-rate、max-concurrency、长 prompt、长输出、shared-prefix、混合流量、长时稳定性
- 数据闭环：JSONL、Prometheus metrics、GPU CSV、图表、阶段文档

## 核心结果

| 场景 | 核心结果 |
|---|---|
| 中压稳定区 | `rr4` 下 `3.80 req/s / 486.87 output tok/s`，p99 E2E `4.06s` |
| 高压退化区 | `rr8` 下 `6.20 req/s / 793.28 output tok/s`，p99 E2E `6.13s` |
| 30 分钟稳定性 | `7200/7200` 成功，`3.96 req/s`，p99 TTFT `432.90ms` |
| 15 分钟高压 | `7200/7200` 成功，但 p99 E2E 升至 `20.76s`，显存逼近上限 |
| shared-prefix 收益 | output throughput 从 `466.28` 提升到 `520.66 tok/s` |
| cache 证据 | cache hit token ratio 从 `0.0023` 提升到 `0.5818` |

一句话结论：

- `rr4` 更适合作为中压稳定区分析
- `rr8` 已进入高压退化区
- shared-prefix 的收益能被 `cached_tokens` 和 `cache_hit_token_ratio` 直接解释

## 关键图表

![Throughput vs Request Rate](figures/final/throughput_vs_request_rate.png)

![P99 vs Request Rate](figures/final/p99_vs_request_rate.png)

![Shared Prefix Cache Hit Ratio](figures/final/shared_prefix_cache_hit_ratio.png)

如果只想快速浏览项目，建议按这个顺序看：

1. 本页 `核心结果`
2. [项目A-公开摘要](项目A-公开摘要.md)
3. [项目A-v2最终结果文档](项目A-v2-最终结果文档.md)
4. [docs/index.md](docs/index.md) 对应的 GitHub Pages 展示页

## 仓库内容

- [项目A-v2最终结果文档](项目A-v2-最终结果文档.md)
- [公开摘要](项目A-公开摘要.md)
- [复现说明](项目A-复现说明.md)
- [简历描述](项目A-v2-简历描述.md)
- [可视化说明](项目A-v2-可视化说明.md)
- [产物清单](ARTIFACTS.md)
- [GitHub 发布说明](GITHUB_PUBLISH.md)

## 目录结构

```text
projectA_v2/
├─ README.md
├─ docs/                     # GitHub Pages 站点入口
├─ figures/final/           # 最终图表
├─ scripts/                 # benchmark / plotting 脚本
├─ 项目A-v2-最终结果文档.md
├─ 项目A-公开摘要.md
├─ 项目A-复现说明.md
└─ 项目A-v2-简历描述.md
```

## 我做了什么

- 固定 `Qwen3-14B tp=4` 服务启动方案并完成接口健康验证。
- 设计并执行生产级压测矩阵，而不是只跑单一 benchmark。
- 建立 JSONL、metrics、GPU CSV、图表之间的一致性链路。
- 用 `cached_tokens` 和 `cache_hit_token_ratio` 解释 shared-prefix 的真实收益。

## 可复现性说明

这个仓库不是“只有结论没有证据”的展示页。

仓库内已经保留：

- 服务启动说明
- benchmark 批量执行脚本
- 混合流量脚本
- 绘图脚本
- 关键图表
- 完整技术报告

为了让仓库更适合公开浏览，原始 `logs / metrics / jsonl / snapshots` 没有全部作为首页展示材料暴露在主阅读路径上，但它们是项目证据链的一部分。项目公开版的结构和保留策略见 [ARTIFACTS.md](ARTIFACTS.md)。

## 进一步阅读

- 完整技术报告见 [项目A-v2最终结果文档](项目A-v2-最终结果文档.md)
- GitHub Pages 入口见 [docs/index.md](docs/index.md)
