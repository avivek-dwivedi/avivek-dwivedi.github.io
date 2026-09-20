# Private LLMOps — Experiment Lab

Reproducible experiment lab for the article
[Private LLMOps for Multi-Agent Systems](https://avivek-dwivedi.github.io/articles/private-llmops-multi-agent.html).

This lab demonstrates **observability concepts** for multi-agent LLM systems using
OpenTelemetry instrumentation. It uses **mock/fake model components** so all
experiments run without burning real API quota or requiring GPU resources.

## Structure

```
experiments/private-llmops/
├── README.md                  This file
├── requirements.txt            Python dependencies
├── app.py                     FastAPI app entry point
├── telemetry.py               OTel + Langfuse setup
├── tracing.py                 Span helpers and context propagation
├── redaction.py               PII/secret redaction processor
├── sampling.py                Head/tail sampling policies
├── agent_runtime.py           Multi-agent workflow runtime
├── tools.py                   Mock tool implementations
├── retrieval.py               Mock retrieval/reranking
├── evaluations.py             Score attachment to traces
├── services/
│   ├── __init__.py
│   ├── agent_a.py             Research agent service
│   └── agent_b.py             Validation agent service
├── mcp/
│   ├── __init__.py
│   ├── client.py              MCP client with trace propagation
│   └── server.py              MCP server with trace context extraction
├── config/
│   └── otel-collector.yaml    OTel Collector configuration
├── experiments/
│   ├── __init__.py
│   ├── trace_overhead.py      Exp 01: instrumentation overhead
│   ├── backend_failure.py     Exp 02: observability backend failure
│   ├── context_propagation.py Exp 03: trace context propagation
│   ├── telemetry_volume.py    Exp 04: full-content vs metadata
│   ├── sampling.py            Exp 05: head vs tail sampling
│   └── cost_latency_attribution.py  Exp 06: cost/latency breakdown
└── results/
    └── .gitkeep               Results land here (empty until runs complete)
```

## Experiments

1. **Observability overhead** — tracing enabled vs disabled, measure p50/p95 latency, CPU, memory
2. **Backend failure** — make telemetry backend unreachable, observe application behavior
3. **Trace context propagation** — broken vs connected traces across service/MCP boundaries
4. **Telemetry volume** — full prompt/response vs metadata-only, measure bytes/event
5. **Sampling** — uniform head sampling vs policy/tail-oriented retention
6. **Cost / latency attribution** — per-agent duration and token breakdown

**No experiments have been executed yet.** Do not add fake result files.

## Running

```bash
pip install -r requirements.txt

# Start the mock workflow server
python app.py

# Run an experiment
python -m experiments.trace_overhead
```

## Design Principles

- **Mock model components** — no real LLM API calls, no quota burned
- **OpenTelemetry instrumentation** — uses standard GenAI semantic conventions
- **Bounded telemetry** — async export with bounded queues
- **Fail-open** — observability failure does not block AI execution
- **Redaction before export** — PII and secrets filtered at source

## Research Basis

- OpenTelemetry GenAI semantic conventions: `github.com/open-telemetry/semantic-conventions-genai` (Development stability, September 2026)
- Langfuse self-hosted architecture (v4): `langfuse.com/self-hosting` (retrieved September 2026)
- W3C Trace Context: `w3.org/TR/trace-context`