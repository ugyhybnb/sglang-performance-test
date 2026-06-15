# 项目A-v2-服务基线

更新日期：2026-06-14

项目定位：**基于 SGLang 的 4 卡 Qwen3-14B 生产级推理服务压测项目**

工作目录：`/home/dell/Kuiperinfer/sglang`

结果目录：`/home/dell/Kuiperinfer/projectA_v2`

## 1. 阶段目标

第二阶段目标是建立正式服务基线：

- 使用 `Qwen3-14B`
- 使用 `4 x RTX 4090 24GB`
- 使用单实例 `tp=4`
- 主接口为 `/v1/chat/completions`
- 开启 `/metrics`
- 开启 cache report
- 固定启动参数、环境信息、验证结果、每卡显存和关键日志

## 2. 阶段结论

`Qwen3-14B` 已在 4 张 RTX 4090 上以单实例 `tp=4` 成功启动。

验收项均已完成：

| 验收项 | 状态 | 证据路径 |
|---|---|---|
| `tp=4` 正式服务启动 | success | `logs/server_qwen3_14b_tp4.log` |
| 环境信息记录 | success | `snapshots/env_20260614_214424.txt` |
| 模型 config/tokenizer 离线验证 | success | `snapshots/model_qwen3_14b_validate_20260614_214424.txt` |
| `/v1/models` 验证 | success | `snapshots/models_20260614_214906.json` |
| `/metrics` 验证 | success | `snapshots/metrics_smoke_20260614_214906.prom` |
| `/v1/chat/completions` non-stream 验证 | success | `snapshots/chat_smoke_nonstream_20260614_214906.json` |
| `/v1/chat/completions` stream 验证 | success | `snapshots/chat_smoke_stream_20260614_214920.jsonl` |
| 每卡显存记录 | success | `snapshots/baseline_gpu_after_start_20260614_214906.csv` |

## 3. 环境与模型

环境快照：

`/home/dell/Kuiperinfer/projectA_v2/snapshots/env_20260614_214424.txt`

关键记录：

| 项 | 值 |
|---|---|
| 仓库 | `/home/dell/Kuiperinfer/sglang` |
| commit | `ebaf86d441447cb37dac92b7bd0838832fcdef48` |
| 运行 Python | `/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python` |
| Python 版本 | `3.12.13` |
| Torch | `2.9.1+cu128` |
| CUDA available | `True` |
| Torch CUDA | `12.8` |
| GPU 数量 | `4` |
| GPU 型号 | `NVIDIA GeForce RTX 4090` |
| 单卡显存 | `24564 MiB` |
| Driver | `550.90.07` |
| nvidia-smi CUDA | `12.4` |

模型路径：

`/home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18`

模型验证结果：

| 项 | 值 |
|---|---|
| model_type | `qwen3` |
| layers | `40` |
| hidden_size | `5120` |
| attention_heads | `40` |
| tokenizer | `Qwen2TokenizerFast` |
| vocab_size | `151643` |
| chat_template | `True` |

## 4. 启动命令

正式启动命令：

```bash
cd /home/dell/Kuiperinfer/sglang
export PYTHONPATH=/home/dell/Kuiperinfer/sglang/python
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_VISIBLE_DEVICES=0,1,2,3

/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python -m sglang.launch_server \
  --model-path /home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18 \
  --served-model-name Qwen3-14B \
  --host 127.0.0.1 \
  --port 30000 \
  --tp-size 4 \
  --mem-fraction-static 0.80 \
  --enable-metrics \
  --enable-cache-report \
  2>&1 | tee /home/dell/Kuiperinfer/projectA_v2/logs/server_qwen3_14b_tp4.log
```

说明：

- `--tp-size 4` 是当前仓库 CLI 对 tensor parallel 的参数名，对应本项目固定服务形态 `tp=4`。
- `--mem-fraction-static 0.80` 本次可稳定启动，作为后续正式压测基线参数。
- 服务进程在实验执行期间保持运行，用于后续 benchmark；全部实验完成后已停止，GPU 已释放。

## 5. 关键启动日志

服务日志：

`/home/dell/Kuiperinfer/projectA_v2/logs/server_qwen3_14b_tp4.log`

关键记录：

```text
server_args ... served_model_name='Qwen3-14B' ... tp_size=4 ... mem_fraction_static=0.8 ... enable_metrics=True ... enable_cache_report=True
Load weight end. type=Qwen3ForCausalLM, dtype=torch.bfloat16, avail mem=16.00 GB, mem usage=7.08 GB.
KV Cache is allocated. #tokens: 298447, K size: 5.69 GB, V size: 5.69 GB
max_total_num_tokens=298447, chunked_prefill_size=2048, max_prefill_tokens=16384, max_running_requests=3730, context_len=40960, available_gpu_mem=2.82 GB
Uvicorn running on http://127.0.0.1:30000
The server is fired up and ready to roll!
```

非阻断 warning：

```text
ModuleNotFoundError: No module named 'openai_harmony'
Can not initialize OpenAIServingResponses
```

该 warning 与 v1 一致，只影响 Responses API 初始化；本项目主接口是 `/v1/chat/completions`，已验证可用。

## 6. 接口验证

`/v1/models` 返回：

```json
{"object":"list","data":[{"id":"Qwen3-14B","object":"model","owned_by":"sglang","root":"Qwen3-14B","max_model_len":40960}]}
```

`/metrics` 关键指标：

```text
sglang:prompt_tokens_total{model_name="Qwen3-14B"} 6.0
sglang:generation_tokens_total{model_name="Qwen3-14B"} 8.0
sglang:num_running_reqs{engine_type="unified",model_name="Qwen3-14B",pp_rank="0",tp_rank="0"} 0.0
sglang:num_queue_reqs{engine_type="unified",model_name="Qwen3-14B",pp_rank="0",tp_rank="0"} 0.0
sglang:cache_hit_rate{engine_type="unified",model_name="Qwen3-14B",pp_rank="0",tp_rank="0"} 0.0
```

chat completions 验证：

- non-stream：`snapshots/chat_smoke_nonstream_20260614_214906.json`
- stream：`snapshots/chat_smoke_stream_20260614_214920.jsonl`

两种模式均成功返回 `Qwen3-14B` 结果。

## 7. GPU 基线

启动后 GPU 快照：

`/home/dell/Kuiperinfer/projectA_v2/snapshots/baseline_gpu_after_start_20260614_214906.csv`

| GPU | 显存占用 | 总显存 | GPU 利用率 |
|---|---:|---:|---:|
| 0 | `21351 MiB` | `24564 MiB` | `0%` |
| 1 | `21351 MiB` | `24564 MiB` | `1%` |
| 2 | `21351 MiB` | `24564 MiB` | `0%` |
| 3 | `21351 MiB` | `24564 MiB` | `0%` |

结论：4 卡显存占用一致，符合单实例 `tp=4` 的正式服务基线。

## 8. 失败与修正记录

| 编号 | 时间 | 尝试 | 现象 | 处理 |
|---|---|---|---|---|
| S2-F001 | 2026-06-14 | 后台 `nohup` 启动 14B 服务 | 进程快速退出且日志为空，无法诊断 | 改为前台会话启动并 `tee` 到服务日志 |
| S2-F002 | 2026-06-14 | 未带 `PYTHONPATH` 查询 `launch_server --help` | `ModuleNotFoundError: No module named 'sglang'` | 使用 `PYTHONPATH=/home/dell/Kuiperinfer/sglang/python` 后重试成功 |
| S2-W001 | 2026-06-14 | 端口 30000 检查 | 旧 `Qwen/Qwen3-0.6B` 服务仍监听端口 | 停止旧服务进程，释放端口后启动正式 14B 服务 |

## 9. 下一步

进入正式压测阶段：

- request-rate stream / non-stream 阶梯
- max-concurrency 阶梯
- 长 prompt 专项
- 长输出专项
- shared-prefix 专项
- 混合流量专项
- 长时稳定性专项
