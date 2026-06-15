# 项目A-v2复现说明

## 1. 目录

工作目录：

`/home/dell/Kuiperinfer/sglang`

结果目录：

`/home/dell/Kuiperinfer/projectA_v2`

## 2. 环境

关键环境快照：

`snapshots/env_20260614_214424.txt`

关键配置：

- Python：`3.12.13`
- Torch：`2.9.1+cu128`
- GPU：`4 x NVIDIA GeForce RTX 4090 24GB`
- Driver：`550.90.07`
- SGLang commit：`ebaf86d441447cb37dac92b7bd0838832fcdef48`

模型路径：

`/home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18`

## 3. 启动服务

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

健康检查：

```bash
curl -sS http://127.0.0.1:30000/v1/models
curl -sS http://127.0.0.1:30000/metrics
curl -sS http://127.0.0.1:30000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen3-14B","messages":[{"role":"user","content":"hello"}],"temperature":0,"max_completion_tokens":32,"stream":false}'
```

## 4. Benchmark 执行

通用 wrapper：

`scripts/run_bench_case.sh`

示例：

```bash
/home/dell/Kuiperinfer/projectA_v2/scripts/run_bench_case.sh rr4_stream \
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
  --request-rate 4 \
  --warmup-requests 2 \
  --disable-tqdm \
  --flush-cache \
  --output-details \
  --output-file /home/dell/Kuiperinfer/projectA_v2/jsonl/rr4_stream.jsonl
```

wrapper 会自动生成：

- `logs/bench_<scenario>.log`
- `jsonl/<scenario>.jsonl`
- `metrics/<scenario>_metrics.prom`
- `metrics/<scenario>_gpu.csv`

混合流量：

```bash
/home/dell/Kuiperinfer/projectA_v2/scripts/run_mixed_case.sh mixed_rr4 \
  --tokenizer /home/dell/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18 \
  --request-rate 4 \
  --output-file /home/dell/Kuiperinfer/projectA_v2/jsonl/mixed_rr4.jsonl
```

## 5. 绘图

```bash
/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python \
  /home/dell/Kuiperinfer/projectA_v2/scripts/plot_projectA_v2.py \
  > /home/dell/Kuiperinfer/projectA_v2/logs/plot_projectA_v2.log 2>&1
```

输出：

- `figures/raw/*.csv`
- `figures/raw/*.png`
- `figures/final/*.png`

## 6. 文档对应关系

| 文档 | 内容 |
|---|---|
| `项目A-v2-服务基线.md` | 服务启动、健康检查、GPU 基线 |
| `项目A-v2-request-rate压测.md` | request-rate 与 stream/non-stream 对照 |
| `项目A-v2-max-concurrency压测.md` | max-concurrency 阶梯 |
| `项目A-v2-长prompt专项.md` | prefill 主导实验 |
| `项目A-v2-长输出专项.md` | decode 主导实验 |
| `项目A-v2-shared-prefix专项.md` | prefix cache 收益 |
| `项目A-v2-混合流量专项.md` | 混合 workload |
| `项目A-v2-长时稳定性专项.md` | 30 分钟和 15 分钟稳定性 |
| `项目A-v2-可视化说明.md` | 图表和数据来源 |
