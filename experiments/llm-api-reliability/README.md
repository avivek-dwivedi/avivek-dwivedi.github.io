# LLM API Reliability — Experiment Lab

Reproducible experiment lab for the article
[Building LLM APIs Under Production Limits](https://avivek-dwivedi.github.io/articles/llm-api-production-limits.html).

This lab uses a **mock provider** so failure conditions can be tested without
burning real API quota. All experiments run against the mock unless a real
provider adapter is explicitly configured.

## Structure

```
experiments/llm-api-reliability/
├── README.md             This file
├── requirements.txt       Python dependencies
├── app.py                FastAPI app entry point
├── gateway.py            Gateway with admission, queue, routing
├── admission.py          Token-aware admission controller
├── budgets.py            RPM / TPM / concurrency budgets
├── queueing.py           Bounded queue management
├── retry.py              Deadline-aware retry with jitter
├── circuit_breaker.py    Circuit breaker state machine
├── router.py             Capability-aware routing
├── streaming.py          Bounded streaming pipeline
├── persistence.py        Durable stream record
├── providers/
│   ├── __init__.py
│   ├── base.py           Provider interface
│   └── mock.py           Mock provider with configurable failures
├── config/
│   └── mock-provider.yaml  Mock provider configuration
├── loadtest/
│   └── run.py            Load test runner
└── results/
    └── .gitkeep          Results land here (empty until runs complete)
```

## Experiments

1. **RPM-only vs RPM+TPM** — heterogeneous request sizes, compare admission policies
2. **Unbounded vs bounded queue** — overload, compare memory and latency
3. **Retry synchronization** — fixed delay vs exponential backoff + full jitter
4. **Retry budget** — unlimited retry vs bounded retry budget during outage
5. **Prompt cache structure** — stable prefix vs dynamic-early (requires real provider)
6. **Stream delivery recovery** — disconnect, reconnect, replay persisted chunks
7. **Provider stream failure** — delivery replay vs generation recovery

No experiments have been executed yet. Do not add fake result files.

## Running

```bash
pip install -r requirements.txt
uvicorn app:app --port 8000
```

Then run load tests:
```bash
python loadtest/run.py
```

## Safety

- Never commit API keys or credentials.
- All credentials come from environment variables.
- Do not commit real secrets.
- The mock provider is for testing failure conditions, not for emulating any
  specific proprietary provider perfectly.