# LLM Inference Engineering — Experiments

Reproducible experiment design for the article
[LLM Inference Engineering: From Prompt to Token](https://avivek-dwivedi.github.io/articles/llm-inference-engineering.html).

No benchmark has been run yet. This directory contains the experiment design and scripts only. Do not add fake result files.

## Files

```
experiments/llm-inference/
├── README.md               This file
├── environment.md          Template — fill with actual environment before publishing results
├── start-server.sh         Starts a local vLLM server
├── benchmark-load.sh        Experiment A — vary concurrency
├── benchmark-prompt-length.sh  Experiment B — vary prompt length
├── ttft_client.py          Small TTFT streaming client (understanding, not harness)
└── results/                Raw results land here (empty until runs are complete)
```

## Experiments

- **Experiment A — Request load:** vary concurrency (1, 4, 8, 16, 32). Measure TTFT, TPOT/ITL, throughput, GPU memory, GPU utilization, KV-cache utilization.
- **Experiment B — Prompt length:** vary prompt size (256, 1024, 4096, 8192). Measure TTFT, end-to-end latency, GPU memory, throughput.
- **Optional Experiment C — Cache pressure:** vary active sequences × context length. Observe KV-cache utilization, GPU memory, TTFT, throughput. Only if measurements can be collected reliably and safely.

## Before running

1. Fill in `environment.md` with the actual model, GPU, CUDA, driver, vLLM and Python versions.
2. Verify `vllm bench serve --help` flags against the installed vLLM version — flags change across releases.
3. Set `MODEL_NAME` in each script to the model you are actually using.
4. Ensure `results/` is the output directory.

## Reproducibility rules

- Publish the full raw result set, not only summaries.
- Do not cherry-pick favorable runs.
- Record the exact command and configuration for every run.
- If a run is discarded, note why in the results directory.
- Every number quoted in the article must be traceable to an artifact in `results/`.

## Safety

- Do not intentionally crash hardware.
- Do not create destructive tests.
- Add 64-concurrency only if the hardware safely supports it.