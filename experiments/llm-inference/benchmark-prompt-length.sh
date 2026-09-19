#!/usr/bin/env bash
# Experiment B — Prompt length sweep.
# Goal: observe how increasing prefill work affects the request,
# holding output length roughly constant and concurrency fixed.
#
# Verify flags against the installed vLLM version before running.
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-MODEL_NAME}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
RESULTS_DIR="${RESULTS_DIR:-./results}"
OUTPUT_LEN="${OUTPUT_LEN:-128}"
CONCURRENCY="${CONCURRENCY:-8}"
NUM_PROMPTS="${NUM_PROMPTS:-50}"
mkdir -p "$RESULTS_DIR"

# Prompt sizes. Only include lengths supported by the model and hardware.
SIZES=(256 1024 4096 8192)

for LEN in "${SIZES[@]}"; do
  echo "=== Prompt length $LEN ==="
  vllm bench serve \
    --backend vllm \
    --model "$MODEL_NAME" \
    --host "$HOST" \
    --port "$PORT" \
    --dataset-name random \
    --random-input-len "$LEN" \
    --random-output-len "$OUTPUT_LEN" \
    --num-prompts "$NUM_PROMPTS" \
    --max-concurrency "$CONCURRENCY" \
    --save-result \
    --result-dir "$RESULTS_DIR" \
    --metric-percentiles "50,95" \
    --percentile-metrics "ttft,e2el"
  echo "--- GPU snapshot ---"
  nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
done

# Notes:
# - Keep output length and concurrency fixed across the sweep.
# - If a length exceeds --max-model-len configured on the server, the server rejects it.
# - Record the rejection behavior; it is correct, not a bug.