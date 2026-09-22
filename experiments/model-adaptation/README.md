# Model Adaptation — Experiment Lab

Reproducible evaluation lab for the article
[Before the First Gradient: Data and Evaluation for Model Adaptation](https://avivek-dwivedi.github.io/articles/before-the-first-gradient.html).

This lab implements the **baseline evaluation methodology** — measuring
non-training interventions before any fine-tuning. It uses **mock model
responses** so the evaluation infrastructure can be tested without GPU
resources or API costs.

## Structure

```
experiments/model-adaptation/
├── README.md
├── requirements.txt
├── config.py               # Task specification and configuration
├── dataset.py              # Synthetic incident dataset generation
├── baselines.py            # Baseline implementations (A-E)
├── evaluation.py           # Scoring and metrics
├── error_analysis.py       # Error categorization
├── contamination.py        # Contamination and dedup checks
├── run_baselines.py        # Run all baselines on the test set
├── run_evaluation.py       # Score and compare results
└── results/
    └── .gitkeep
```

## Experiment

**Question:** Does any non-training intervention resolve the task's failures,
and what is the error distribution that would justify weight adaptation?

**Baselines:**
- A: Frozen base model, basic prompt
- B: Frozen model, optimized prompt (few-shot)
- C: Frozen model, structured output constraints
- D: Frozen model + retrieval (mock context)
- E: Alternative model

**No experiments have been executed yet.** Do not add fake result files.

## Running

```bash
pip install -r requirements.txt

# Generate the synthetic dataset
python -m dataset --output data/incidents.jsonl

# Run all baselines
python run_baselines.py

# Score and compare
python run_evaluation.py
```

## Design Principles

- **Mock model responses** — no real API calls, no GPU needed
- **Controlled comparison** — all baselines evaluated on the same test set
- **Error taxonomy defined before evaluation** — not post-hoc
- **Synthetic data** — no pretraining contamination, no customer data
- **Test set touched once** — never tune against it