#!/usr/bin/env bash
# Start a local vLLM OpenAI-compatible server.
# Verify flags against the installed vLLM version — flags change across releases.
set -euo pipefail

# Set to the model you are actually using.
MODEL_NAME="${MODEL_NAME:-MODEL_NAME}"

# Example server startup. Adjust flags for your hardware and model.
vllm serve "$MODEL_NAME" \
  --dtype auto \
  --max-model-len 8192 \
  --host 127.0.0.1 \
  --port 8000

# Notes:
# - For multi-GPU, add --tensor-parallel-size N (verify against your version).
# - For quantized models, add the appropriate quantization flag.
# - Do not hardcode a model in the article; set it here before running.