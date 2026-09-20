"""
Experiment 06 — Multi-Agent Cost / Latency Attribution

Question: How is cost and latency distributed across agents in a workflow?

Procedure:
  Create one workflow with several agent/model/tool steps.
  Capture: duration per step, token count (simulated), relative cost (simulated).
  Produce a trace breakdown.

All values are SYNTHETIC — labeled as synthetic workload, not production measurements.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List

from tracing import (
    workflow_span, agent_span, generation_span, tool_span,
    retrieval_span, set_token_usage,
)
from tools import execute_tool
from retrieval import retrieve
import random


# Simulated price table (SYNTHETIC — not real provider prices)
# In production, maintain a versioned price table with retrieval dates.
SYNTHETIC_PRICES = {
    "mock-gpt-4": {"input": 0.00003, "output": 0.00006},  # per token, synthetic
    "mock-gpt-4-mini": {"input": 0.00001, "output": 0.00003},
}


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute synthetic cost for a generation."""
    prices = SYNTHETIC_PRICES.get(model, {"input": 0.00002, "output": 0.00004})
    return (input_tokens * prices["input"]) + (output_tokens * prices["output"])


def run_attribution_experiment() -> Dict[str, Any]:
    """Run a workflow and collect per-step cost/latency attribution."""
    results: Dict[str, Any] = {
        "experiment": "cost_latency_attribution",
        "status": "not_executed",
        "steps": [],
        "total_cost": 0.0,
        "total_latency_ms": 0.0,
        "total_tokens": 0,
        "label": "synthetic_workload",
    }

    start = time.time()

    with workflow_span("attribution_test", version="1.0.0"):
        # Step 1: Planner agent
        t0 = time.time()
        with agent_span("planner", "1.0.0"):
            with generation_span(model="mock-gpt-4") as gen:
                time.sleep(random.uniform(0.3, 0.5))
                inp, out = random.randint(100, 300), random.randint(50, 150)
                set_token_usage(gen, inp, out)
        step1_ms = (time.time() - t0) * 1000
        step1_cost = compute_cost("mock-gpt-4", inp, out)
        results["steps"].append({
            "agent": "planner", "model": "mock-gpt-4",
            "latency_ms": step1_ms, "input_tokens": inp, "output_tokens": out,
            "cost": step1_cost,
        })

        # Step 2: Research agent (retrieval + tool + generation)
        t0 = time.time()
        with agent_span("research_agent", "2.1.0"):
            with retrieval_span():
                retrieve("test query", top_k=5)
            with tool_span("kb.search"):
                execute_tool("kb.search", query="test", top_k=3)
            with generation_span(model="mock-gpt-4") as gen:
                time.sleep(random.uniform(0.4, 0.8))
                inp, out = random.randint(200, 500), random.randint(100, 300)
                set_token_usage(gen, inp, out)
        step2_ms = (time.time() - t0) * 1000
        step2_cost = compute_cost("mock-gpt-4", inp, out)
        results["steps"].append({
            "agent": "research_agent", "model": "mock-gpt-4",
            "latency_ms": step2_ms, "input_tokens": inp, "output_tokens": out,
            "cost": step2_cost,
        })

        # Step 3: Validation agent
        t0 = time.time()
        with agent_span("validation_agent", "1.5.0"):
            with tool_span("validate.response"):
                execute_tool("validate.response", response="test")
            with generation_span(model="mock-gpt-4-mini") as gen:
                time.sleep(random.uniform(0.2, 0.4))
                inp, out = random.randint(100, 200), random.randint(30, 80)
                set_token_usage(gen, inp, out)
        step3_ms = (time.time() - t0) * 1000
        step3_cost = compute_cost("mock-gpt-4-mini", inp, out)
        results["steps"].append({
            "agent": "validation_agent", "model": "mock-gpt-4-mini",
            "latency_ms": step3_ms, "input_tokens": inp, "output_tokens": out,
            "cost": step3_cost,
        })

        # Step 4: Final generation
        t0 = time.time()
        with generation_span(model="mock-gpt-4") as gen:
            time.sleep(random.uniform(0.3, 0.6))
            inp, out = random.randint(300, 600), random.randint(100, 200)
            set_token_usage(gen, inp, out)
        step4_ms = (time.time() - t0) * 1000
        step4_cost = compute_cost("mock-gpt-4", inp, out)
        results["steps"].append({
            "agent": "final_generation", "model": "mock-gpt-4",
            "latency_ms": step4_ms, "input_tokens": inp, "output_tokens": out,
            "cost": step4_cost,
        })

    results["total_latency_ms"] = (time.time() - start) * 1000
    results["total_cost"] = sum(s["cost"] for s in results["steps"])
    results["total_tokens"] = sum(s["input_tokens"] + s["output_tokens"] for s in results["steps"])
    results["status"] = "executed"

    return results


if __name__ == "__main__":
    from telemetry import init_telemetry, shutdown_telemetry

    init_telemetry(enable_otlp=False, enable_console=True)

    print("=" * 60)
    print("Experiment 06: Cost / Latency Attribution")
    print("=" * 60)
    print()
    print("Methodology:")
    print("  Run a 4-step multi-agent workflow with per-step instrumentation.")
    print("  Capture: duration, tokens, cost per step.")
    print("  Prices are SYNTHETIC — not real provider prices.")
    print()

    results = run_attribution_experiment()

    print(f"\nResults (label: {results['label']}):")
    print(f"  Total latency: {results['total_latency_ms']:.1f} ms")
    print(f"  Total cost: ${results['total_cost']:.6f} (synthetic)")
    print(f"  Total tokens: {results['total_tokens']}")
    print()
    print(f"  {'Agent':<25} {'Latency (ms)':>12} {'Tokens':>8} {'Cost ($)':>12} {'% latency':>10}")
    print(f"  {'-'*25} {'-'*12} {'-'*8} {'-'*12} {'-'*10}")
    for step in results["steps"]:
        pct = (step["latency_ms"] / results["total_latency_ms"]) * 100
        tokens = step["input_tokens"] + step["output_tokens"]
        print(f"  {step['agent']:<25} {step['latency_ms']:>12.1f} {tokens:>8} {step['cost']:>12.6f} {pct:>9.1f}%")
    print()
    print("NOTE: Synthetic workload. Cost values are based on fake price table.")
    print("Do not present as production cost measurements.")

    shutdown_telemetry()