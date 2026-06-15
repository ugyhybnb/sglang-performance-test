# 项目A-v2 简历描述

## 推荐版

基于 SGLang 在 `4 x RTX 4090 24GB` 上部署 `Qwen3-14B` 单实例 `tp=4` 在线推理服务，围绕 `/v1/chat/completions` 设计并执行生产级压测矩阵，覆盖 request-rate、max-concurrency、长 prompt、长输出、shared-prefix、混合流量和长时稳定性。构建 JSONL、Prometheus metrics、GPU 采样和图表闭环，定位 `rr4` 为中压稳定区，`rr8` 为高压退化边界，并通过 `cached_tokens` 证明 shared-prefix 场景下 prefix cache 命中率从 `0.0023` 提升到 `0.5818`。

## 两条版

- 基于 SGLang 在 `4 x RTX 4090 24GB` 上搭建 `Qwen3-14B tp=4` 在线推理服务，围绕 `/v1/chat/completions` 完成 request-rate、max-concurrency、长 prompt、长输出、shared-prefix、混合流量和长时稳定性压测。
- 沉淀 JSONL、Prometheus metrics、GPU 采样和可视化图表，识别 `rr4` 为中压稳定区、`rr8` 为高压退化边界，并用 `cached_tokens` 证明 shared-prefix 的 cache hit token ratio 从 `0.0023` 提升到 `0.5818`。

## 三条版

- 基于 SGLang 在 `4 x RTX 4090 24GB` 上部署 `Qwen3-14B` 单实例 `tp=4` 在线推理服务，固定 `/v1/chat/completions` 为主接口，完成服务基线、环境记录、日志与 metrics 采集闭环。
- 设计并执行生产级压测矩阵，覆盖 request-rate、max-concurrency、长 prompt、长输出、shared-prefix、混合流量和长时稳定性，沉淀 benchmark JSONL、Prometheus 指标、GPU 采样与图表。
- 定位 `rr4` 为中压稳定区、`rr8` 为高压退化边界；验证 shared-prefix 场景下 output throughput 从 `466.28` 提升到 `520.66 tok/s`，cache hit token ratio 从 `0.0023` 提升到 `0.5818`。

## 超短版

基于 SGLang 在 `4 x RTX 4090` 上部署 `Qwen3-14B tp=4` 在线推理服务，完成生产级压测与可视化分析，覆盖容量边界、长 prompt、长输出、shared-prefix、混合流量和长时稳定性，并用 `cached_tokens` 量化 prefix cache 收益。

## 面试官关注点

- 这个项目的强点不在“跑通服务”，而在“把 4 卡 14B 服务做成了可压测、可观测、可解释的系统项目”。
- 讲述时优先强调服务形态、指标体系、容量边界、shared-prefix 证据链和长时稳定性。
- 不要把重心放在单卡背景、小模型 smoke 或 benchmark 命令本身。
