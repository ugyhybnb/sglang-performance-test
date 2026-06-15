#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <scenario> <bench_serving args...>" >&2
  exit 2
fi

SCENARIO="$1"
shift

OUT_DIR="${OUT_DIR:-/home/dell/Kuiperinfer/projectA_v2}"
SGLANG_DIR="${SGLANG_DIR:-/home/dell/Kuiperinfer/sglang}"
PY="${PY:-/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-30000}"

LOG="${OUT_DIR}/logs/bench_${SCENARIO}.log"
METRICS="${OUT_DIR}/metrics/${SCENARIO}_metrics.prom"
GPU="${OUT_DIR}/metrics/${SCENARIO}_gpu.csv"

mkdir -p "${OUT_DIR}/logs" "${OUT_DIR}/metrics" "${OUT_DIR}/jsonl"

metrics_pid=""
gpu_pid=""

cleanup() {
  if [[ -n "${metrics_pid}" ]] && kill -0 "${metrics_pid}" 2>/dev/null; then
    kill "${metrics_pid}" 2>/dev/null || true
    wait "${metrics_pid}" 2>/dev/null || true
  fi
  if [[ -n "${gpu_pid}" ]] && kill -0 "${gpu_pid}" 2>/dev/null; then
    kill "${gpu_pid}" 2>/dev/null || true
    wait "${gpu_pid}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

(
  while true; do
    printf '# timestamp %s\n' "$(date --iso-8601=ns)"
    curl -sS "http://${HOST}:${PORT}/metrics" \
      | rg 'sglang:(num_running_reqs|num_queue_reqs|cache_hit_rate|prompt_tokens_total|generation_tokens_total|e2e_request_latency|time_to_first_token|inter_token_latency)' || true
    sleep 1
  done
) > "${METRICS}" 2>&1 &
metrics_pid="$!"

nvidia-smi \
  --query-gpu=timestamp,index,name,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu \
  --format=csv,nounits \
  -l 1 \
  > "${GPU}" 2>&1 &
gpu_pid="$!"

{
  echo "# scenario: ${SCENARIO}"
  echo "# start: $(date --iso-8601=seconds)"
  echo "# workdir: ${SGLANG_DIR}"
  echo "# command: ${PY} -m sglang.bench_serving $*"
  echo "# metrics: ${METRICS}"
  echo "# gpu: ${GPU}"
  cd "${SGLANG_DIR}"
  export PYTHONPATH="${SGLANG_DIR}/python"
  export HF_HUB_OFFLINE=1
  export TRANSFORMERS_OFFLINE=1
  "${PY}" -m sglang.bench_serving "$@"
  status=$?
  echo "# end: $(date --iso-8601=seconds)"
  echo "# exit_status: ${status}"
  exit "${status}"
} > "${LOG}" 2>&1
