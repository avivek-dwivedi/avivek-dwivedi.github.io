#!/usr/bin/env bash
# Experiment A — Request load / concurrency sweep.
# Goal: observe how TTFT, TPOT/ITL, throughput, GPU memory, GPU utilization
# change as concurrency increases.
#
# Verify flags against the installed vLLM version before running.
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-MODEL_NAME}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
RESULTS_DIR="${RESULTS_DIR:-./results}"
INPUT_LEN="${INPUT_LEN:-1024}"
OUTPUT_LEN="${OUTPUT_LEN:-128}"
mkdir -p "$RESULTS_DIR"

# Concurrency levels. Add 64 only if hardware safely supports it.
LEVELS=(1 4 8 16 32)

for N in "${LEVELS[@]}"; do
  echo "=== Concurrency $N ==="
  vllm bench serve \
    --backend vllm \
    --model "$MODEL_NAME" \
    --host "$HOST" \
    --port "$PORT" \
    --dataset-name random \
    --random-input-len "$INPUT_LEN" \
    --random-output-len "$OUTPUT_LEN" \
    --num-prompts "$N" \
    --max-concurrency "$N" \
    --request-rate "$N" \
    --save-result \
    --result-dir "$RESULTS_DIR" \
    --metric-percentiles "50,95" \
    --percentile-metrics "ttft,tpot,itl,e2el"
  echo "--- GPU snapshot ---"
  nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
done

# Notes:
# - request-rate set equal to concurrency for a steady load; adjust as needed.
# - Adjust metric-percentiles/percentile-metrics flags to your vLLM version.
# - Keep model, dtype, input/output length fixed across the sweep.