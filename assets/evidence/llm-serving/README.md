# Evidence — LLM Serving

This directory holds experiment evidence for the article
[Designing Production LLM Serving Systems](https://avivek-dwivedi.github.io/articles/production-llm-serving.html).

No experiment has been run yet. When experiments are performed, raw artifacts
will be stored here and linked from the article.

## Expected file layout

When the experiments in Section 10 of the article are completed, this directory
should contain:

```
assets/evidence/llm-serving/
├── baseline-terminal.png      # Experiment 01 — baseline serving output
├── grafana-ttft.png            # TTFT panel captured during runs
├── queue-pressure.png          # Experiment 02 — queue pressure
├── autoscaling.png             # Experiment 03 — replica scaling
├── failure-recovery.png        # Experiment 04 — failure / restart
└── raw-results.csv             # Raw numeric results for all experiments
```

Do not add placeholder images. Add real artifacts only after the corresponding
run is complete.

## Required metadata for every experiment

Each experiment must publish the following metadata alongside its artifacts.
Use a `metadata.json` (or a section in `raw-results.csv`) per run:

- **hardware** — GPU model, count, host CPU, RAM
- **model** — exact model name and revision
- **software versions** — vLLM version, KServe version, Kubernetes version,
  Python version, CUDA version, GPU driver version
- **command** — the exact benchmark / serving command used
- **configuration** — tensor-parallel size, max-model-len, gpu-memory-utilization,
  quantization, batch policy, concurrency settings
- **date** — ISO-8601 date of the run
- **raw results** — link to the raw CSV / log, not only summaries

## Reproducibility rules

- Do not cherry-pick favorable runs; publish the full raw set.
- Do not edit screenshots; if a panel needs context, add a caption in the
  article, not an altered image.
- If a run is discarded, note why in the raw results file.
- Every number quoted in the article must be traceable to an artifact here.

## Source

A GitHub repository link will be added when the experiment repository is
available. Do not invent a repository.