# sglang-performance-test final report

完成日期：2026-06-14

## 1. 项目目标

sglang-performance-test 定位为：

**基于 SGLang 的 4 卡 Qwen3-14B 生产级推理服务压测项目**

目标是在 `4 x RTX 4090 24GB` 上使用 SGLang 单实例 `tp=4` 部署 `Qwen3-14B`，以 `/v1/chat/completions` 为主接口，完成容量边界、长尾时延、prefix cache、混合流量和长时稳定性分析。

项目边界：

- 不做单卡教学式对照
- 不做 vLLM 横评
- 不做量化
- 不做 speculative decoding
- 不做 kernel 优化
- 不改写调度算法
- 小模型只用于背景和 smoke，不进入 v2 正式结论

## 2. 环境与模型

| 项 | 值 |
|---|---|
| SGLang commit | `ebaf86d441447cb37dac92b7bd0838832fcdef48` |
| Python | `3.12.13` |
| Torch | `2.9.1+cu128` |
| GPU | `4 x NVIDIA GeForce RTX 4090 24GB` |
| Driver | `550.90.07` |
| 模型 | `Qwen3-14B` |
| 模型路径 | `/home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18` |
| dtype | bf16 |

证据：

- `snapshots/env_20260614_214424.txt`
- `snapshots/model_qwen3_14b_validate_20260614_214424.txt`

## 3. 4 卡服务启动方案

启动命令见：

`sglang-performance-test-reproduction.md`

核心参数：

- `--served-model-name Qwen3-14B`
- `--tp-size 4`
- `--mem-fraction-static 0.80`
- `--enable-metrics`
- `--enable-cache-report`

关键启动结果：

- `Qwen3ForCausalLM`
- `dtype=torch.bfloat16`
- KV cache tokens：`298447`
- context length：`40960`
- 启动后每卡显存约 `21351 MiB`

健康检查：

- `/v1/models`：成功返回 `Qwen3-14B`
- `/metrics`：包含 running、queue、cache、token 指标
- `/v1/chat/completions`：stream 与 non-stream 均成功

## 4. 正式压测矩阵

| 阶段 | 说明 |
|---|---|
| request-rate + stream/non-stream | 基线容量与长尾时延 |
| max-concurrency | 并发限制与吞吐变化 |
| 长 prompt | prefill 主导场景 |
| 长输出 | decode 主导场景 |
| shared-prefix | prefix cache 收益 |
| 混合流量 | 多类请求互相影响 |
| 长时稳定性 | 中压与高压持续运行表现 |

每个实验均记录：

- benchmark stdout 日志
- JSONL 结果
- SGLang metrics 采样
- GPU CSV 采样
- 阶段文档

## 5. 基线容量结果

request-rate streaming 结果：

| rr | req/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms |
|---:|---:|---:|---:|---:|---:|---:|
| 0.5 | 0.54 | 68.69 | 113.32 | 163.66 | 1524.74 | 1768.96 |
| 1 | 1.06 | 135.07 | 109.98 | 183.09 | 1626.41 | 2091.33 |
| 2 | 2.04 | 260.87 | 112.21 | 217.73 | 1881.51 | 2658.36 |
| 4 | 3.80 | 486.87 | 127.57 | 246.26 | 2935.07 | 4064.39 |
| 8 | 6.20 | 793.28 | 218.36 | 563.21 | 4768.74 | 6129.57 |

结论：

- rr2 以内首 token 延迟较稳。
- rr4 开始 E2E 和 TPOT 明显放大。
- rr8 吞吐继续增加，但已经进入高压退化区。

## 6. 长 prompt 专项

| prompt | req/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms |
|---:|---:|---:|---:|---:|---:|
| 512 | 1.38 | 105.67 | 152.26 | 888.24 | 1048.54 |
| 2048 | 1.34 | 382.19 | 639.57 | 1643.72 | 2358.48 |
| 4096 | 1.23 | 1198.41 | 1937.58 | 6269.05 | 12551.00 |
| 8192 | 0.76 | 5710.95 | 13209.64 | 21130.01 | 31587.89 |

结论：`4096` 以后 prefill 成本和长尾明显恶化，`8192` 已进入强 prefill 压力区。

## 7. 长输出专项

| output | req/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms | mean TPOT ms |
|---:|---:|---:|---:|---:|---:|---:|
| 64 | 1.38 | 107.10 | 153.75 | 888.50 | 1058.92 | 12.13 |
| 128 | 1.32 | 110.34 | 151.15 | 1679.18 | 1906.19 | 12.31 |
| 256 | 1.21 | 110.89 | 153.68 | 3498.09 | 3773.17 | 13.12 |

结论：输出变长主要拉高 E2E 和请求驻留时间，对 TTFT 影响较小。

## 8. shared-prefix 专项

rr4 streaming 对照：

| workload | req/s | output tok/s | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms |
|---|---:|---:|---:|---:|---:|---:|
| random | 3.64 | 466.28 | 556.07 | 1024.48 | 5687.26 | 7928.80 |
| shared-prefix | 4.07 | 520.66 | 130.00 | 836.31 | 2544.20 | 4406.50 |

non-stream cache 证据：

| workload | cached tokens | cache hit ratio |
|---|---:|---:|
| random | 90 | 0.0023 |
| shared-prefix | 22671 | 0.5818 |

结论：shared-prefix 的吞吐和延迟收益能由 `cached_tokens` 直接解释。

## 9. 混合流量专项

| 类型 | 请求数 | p50 TTFT ms | p99 TTFT ms | p50 E2E ms | p99 E2E ms |
|---|---:|---:|---:|---:|---:|
| short_qa | 12 | 96.26 | 734.77 | 1887.62 | 3265.71 |
| long_prompt | 8 | 746.21 | 1029.53 | 2042.72 | 4102.91 |
| long_output | 8 | 359.06 | 893.12 | 6651.99 | 8772.33 |
| shared_prefix | 16 | 310.66 | 789.26 | 3982.12 | 5850.65 |

结论：

- long_prompt 最伤 TTFT。
- long_output 最伤 E2E。
- short_qa 会被混合流量拖慢。
- shared-prefix 收益在混合流量中会被长请求稀释。

## 10. 长时稳定性专项

| 场景 | 成功请求 | 时长 s | req/s | p99 TTFT ms | p99 E2E ms | max queue | 显存 max MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| rr4 30min | 7200 | 1818.51 | 3.96 | 432.90 | 5422.32 | 0 | 21561 |
| rr8 15min | 7200 | 918.11 | 7.84 | 753.89 | 20761.55 | 2 | 23747 |

结论：

- rr4 可稳定持续 30 分钟，无错误和 timeout。
- rr8 能完成高压 15 分钟，但 p99 E2E 超过 20s，显存接近 24GB 上限，不适合作为稳定 SLO。

## 11. 失败尝试与修正

| 编号 | 阶段 | 失败或风险 | 修正 |
|---|---|---|---|
| F-001 | 服务基线 | 旧 `Qwen/Qwen3-0.6B` 服务占用 30000 端口 | 停止旧服务，释放端口后启动正式 14B |
| F-002 | 服务基线 | 未带 `PYTHONPATH` 查询 `launch_server` 失败 | 使用 `PYTHONPATH=/home/dell/Kuiperinfer/sglang/python` |
| F-003 | 服务基线 | 后台 `nohup` 启动日志为空，无法诊断 | 改为前台会话并 `tee` 写服务日志 |
| F-004 | 可视化 | CSV 行字段不一致导致绘图失败 | 修正 `plot_projectA_v2.py` 的 CSV 字段合并逻辑 |

公开版仅保留与最终结论直接相关的失败条目；内部工作台账未纳入公开仓库。

## 12. 最终结论

`Qwen3-14B` 在 `4 x RTX 4090 24GB` 上以 SGLang 单实例 `tp=4` 可以稳定启动并完成生产化压测闭环。

容量判断：

- `rr4` 是较合理的中压稳定区：30 分钟无失败，p99 TTFT `432.90ms`，p99 E2E `5.42s`。
- `rr8` 是高压上界/退化区：吞吐高，但 p99 E2E `20.76s`，显存最高 `23747 MiB`。

workload 判断：

- 长 prompt 主要伤 TTFT。
- 长输出主要伤 E2E 和并发驻留。
- shared-prefix 可以通过 prefix cache 明显降低重复 prefill 成本。
- 混合流量会让短请求也被长请求拖慢。

## 13. 关键图表

图表说明见：

`sglang-performance-test-visualization.md`

核心图：

- `figures/final/throughput_vs_request_rate.png`
- `figures/final/p99_vs_request_rate.png`
- `figures/final/ttft_vs_request_rate.png`
- `figures/final/long_prompt_ttft.png`
- `figures/final/long_output_e2e_tpot.png`
- `figures/final/shared_prefix_throughput.png`
- `figures/final/shared_prefix_cache_hit_ratio.png`
- `figures/final/gpu_memory_stability.png`
- `figures/final/queue_running_stability.png`

## 14. 简历描述

基于 SGLang 在 `4 x RTX 4090 24GB` 上部署 `Qwen3-14B` 单实例 `tp=4` 在线推理服务，围绕 `/v1/chat/completions` 设计并执行生产级压测矩阵，覆盖 request-rate、max-concurrency、长 prompt、长输出、shared-prefix、混合流量和长时稳定性。沉淀 JSONL、Prometheus metrics、GPU 采样和可视化图表，定位 rr4 为中压稳定区，rr8 为高压退化边界，并通过 `cached_tokens` 证明 shared-prefix 场景下 prefix cache 命中率从 `0.0023` 提升到 `0.5818`。

## 15. 3 分钟面试讲述稿

这个项目的目标不是简单跑通 SGLang，而是在 4 张 4090 上把 `Qwen3-14B` 做成一个可压测、可观测、可复现的在线推理服务。我使用 SGLang 单实例 `tp=4` 启动服务，固定 `/v1/chat/completions` 为主接口，开启 metrics 和 cache report，并记录启动日志、GPU 显存、接口健康检查和模型信息。

压测部分我没有只跑一个 benchmark，而是设计了多个生产视角的 workload：request-rate 阶梯用来找容量边界，max-concurrency 阶梯用来看上游并发限制影响，长 prompt 和长输出分别对应 prefill 主导和 decode 主导场景，shared-prefix 用来验证 prefix cache，混合流量用来观察真实线上不同请求互相干扰，最后做了 30 分钟中压和 15 分钟高压稳定性。

结果上，rr4 是比较稳定的中压点，30 分钟内 7200 个请求全部成功，p99 TTFT 约 433ms，p99 E2E 约 5.42s；rr8 虽然吞吐能到 7.84 req/s，但 p99 E2E 超过 20s，显存接近 24GB 上限，所以我把它定义为高压退化边界。机制上，shared-prefix 场景的 cache hit token ratio 达到 0.5818，而随机对照只有 0.0023，说明吞吐和延迟收益确实来自 prefix cache 复用。

最终这个项目沉淀了服务基线、完整压测结果、失败记录、图表、公开摘要和复现说明，可以从工程启动、指标采集、机制解释和生产 SLO 四个角度讲清楚。
