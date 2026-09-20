"""
Experiment 01 — Observability Overhead

Question: What does tracing cost in latency and memory?

Procedure:
  A: Run the workflow with instrumentation disabled
  B: Run the workflow with OTel instrumentation enabled (async/batched export)

Measure: p50 latency, p95 latency, CPU, memory, telemetry bytes

NOT EXECUTED. This script defines methodology and instrumentation.
Run it to collect results. Do not publish results until real runs complete.
"""

from __future__ import annotations

import time
import os
import tracemalloc
import statistics
from typing import List, Dict, Any

# NOTE: Import telemetry only when needed for the instrumented run.
# For the non-instrumented run, we skip OTel initialization entirely.


def run_experiment(num_iterations: int = 50) -> Dict[str, Any]:
    """
    Run the overhead experiment.

    Returns a results dictionary. Results are NOT published until
    the experiment is actually run and verified.
    """
    from agent_runtime import run_workflow

    results: Dict[str, Any] = {
        "experiment": "observability_overhead",
        "iterations": num_iterations,
        "status": "not_executed",
        "runs_a": [],  # Without instrumentation
        "runs_b": [],  # With instrumentation
    }

    # --- Run A: No instrumentation ---
    print(f"Run A: {num_iterations} iterations WITHOUT instrumentation")
    tracemalloc.start()
    for i in range(num_iterations):
        start = time.time()
        run_workflow(f"test query {i}", enable_telemetry=False)
        elapsed_ms = (time.time() - start) * 1000
        results["runs_a"].append({"iteration": i, "latency_ms": elapsed_ms})
    _, peak_a = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    results["peak_memory_a_bytes"] = peak_a

    # --- Run B: With instrumentation ---
    from telemetry import init_telemetry, shutdown_telemetry
    print(f"Run B: {num_iterations} iterations WITH instrumentation")
    init_telemetry(enable_otlp=False, enable_console=True)  # Console for local test
    tracemalloc.start()
    for i in range(num_iterations):
        start = time.time()
        run_workflow(f"test query {i}", enable_telemetry=True)
        elapsed_ms = (time.time() - start) * 1000
        results["runs_b"].append({"iteration": i, "latency_ms": elapsed_ms})
    _, peak_b = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    results["peak_memory_b_bytes"] = peak_b
    shutdown_telemetry()

    # --- Compute statistics ---
    latencies_a = [r["latency_ms"] for r in results["runs_a"]]
    latencies_b = [r["latency_ms"] for r in results["runs_b"]]

    results["p50_a"] = statistics.median(latencies_a)
    results["p95_a"] = _percentile(latencies_a, 95)
    results["p50_b"] = statistics.median(latencies_b)
    results["p95_b"] = _percentile(latencies_b, 95)
    results["overhead_p50_ms"] = results["p50_b"] - results["p50_a"]
    results["overhead_p95_ms"] = results["p95_b"] - results["p95_a"]
    results["memory_overhead_bytes"] = peak_b - peak_a
    results["status"] = "executed"

    return results


def _percentile(data: List[float], p: float) -> float:
    """Compute the p-th percentile of a list."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100.0
    f = int(k)
    c = k - f
    if f + 1 < len(sorted_data):
        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
    return sorted_data[f]


if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 01: Observability Overhead")
    print("=" * 60)
    print()
    print("Methodology:")
    print("  A: Workflow without OTel instrumentation")
    print("  B: Workflow with OTel instrumentation (async/batched)")
    print("  Measure: p50, p95 latency, peak memory")
    print()

    results = run_experiment(num_iterations=20)

    print()
    print("Results (label: synthetic workload):")
    print(f"  P50 A (no telemetry): {results['p50_a']:.1f} ms")
    print(f"  P50 B (with telemetry): {results['p50_b']:.1f} ms")
    print(f"  P50 overhead: {results['overhead_p50_ms']:.1f} ms")
    print(f"  P95 A (no telemetry): {results['p95_a']:.1f} ms")
    print(f"  P95 B (with telemetry): {results['p95_b']:.1f} ms")
    print(f"  P95 overhead: {results['overhead_p95_ms']:.1f} ms")
    print(f"  Peak memory A: {results['peak_memory_a_bytes']:,} bytes")
    print(f"  Peak memory B: {results['peak_memory_b_bytes']:,} bytes")
    print(f"  Memory overhead: {results['memory_overhead_bytes']:,} bytes")
    print()
    print("NOTE: These are synthetic workload measurements from a mock lab.")
    print("Do not present as production benchmarks.")