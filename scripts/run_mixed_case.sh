#!/usr/bin/env bash
set -euo pipefail

SCENARIO="${1:?scenario required}"
shift

OUT_DIR="${OUT_DIR:-/home/dell/Kuiperinfer/projectA_v2}"
PY="${PY:-/home/dell/Kuiperinfer/mini-sglang/.venv/bin/python}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-30000}"

LOG="${OUT_DIR}/logs/mixed_${SCENARIO}.log"
METRICS="${OUT_DIR}/metrics/${SCENARIO}_metrics.prom"
GPU="${OUT_DIR}/metrics/${SCENARIO}_gpu.csv"

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
  echo "# command: ${PY} /home/dell/Kuiperinfer/projectA_v2/scripts/run_mixed_traffic.py $*"
  echo "# metrics: ${METRICS}"
  echo "# gpu: ${GPU}"
  export HF_HUB_OFFLINE=1
  export TRANSFORMERS_OFFLINE=1
  "${PY}" /home/dell/Kuiperinfer/projectA_v2/scripts/run_mixed_traffic.py "$@"
  status=$?
  echo "# end: $(date --iso-8601=seconds)"
  echo "# exit_status: ${status}"
  exit "${status}"
} > "${LOG}" 2>&1
