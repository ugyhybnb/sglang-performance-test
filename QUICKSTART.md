# Quickstart

## 1. Environment

- Python `3.12`
- Torch `2.9.1+cu128`
- `4 x RTX 4090 24GB`
- SGLang commit `ebaf86d441447cb37dac92b7bd0838832fcdef48`

## 2. Start the service

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
  --enable-cache-report
```

## 3. Check the service

```bash
curl -sS http://127.0.0.1:30000/v1/models
curl -sS http://127.0.0.1:30000/metrics
```

## 4. Run one benchmark case

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

## 5. Plot figures

```bash
/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python \
  /home/dell/Kuiperinfer/projectA_v2/scripts/plot_projectA_v2.py
```

## 6. Read the results

- Final report: `项目A-v2-最终结果文档.md`
- Reproduction notes: `项目A-复现说明.md`
- Visualization notes: `项目A-v2-可视化说明.md`
