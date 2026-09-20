"""
Experiment 02 — Backend Failure

Question: What happens if the observability backend becomes unavailable?

Procedure:
  1. Start the workflow with telemetry enabled
  2. Make the telemetry backend unreachable (point OTLP to a dead endpoint)
  3. Continue running requests
  4. Observe: application success, exporter queue, memory, errors, dropped telemetry

Hypothesis:
  - Fail-open architecture: AI execution continues
  - Bounded queue prevents OOM
  - Telemetry is dropped or buffered, not blocking

NOT EXECUTED. This script defines methodology.
"""

from __future__ import annotations

import time
import os
import tracemalloc
from typing import Dict, Any, List


def run_experiment(num_iterations: int = 30) -> Dict[str, Any]:
    """
    Run the backend failure experiment.

    Points the OTLP exporter at a dead endpoint to simulate backend unavailability.
    Measures whether the application continues to function.
    """
    # Set a dead OTLP endpoint BEFORE importing telemetry
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:9999"
    # Small queue to trigger backpressure quickly
    os.environ["OTEL_BSP_MAX_QUEUE_SIZE"] = "100"

    from telemetry import init_telemetry, shutdown_telemetry
    from agent_runtime import run_workflow

    results: Dict[str, Any] = {
        "experiment": "backend_failure",
        "iterations": num_iterations,
        "status": "not_executed",
        "otel_endpoint": "http://localhost:9999 (dead)",
        "queue_size": 100,
        "runs": [],
    }

    print("Initializing telemetry with DEAD backend endpoint...")
    init_telemetry(enable_otlp=True, enable_console=False)

    tracemalloc.start()
    for i in range(num_iterations):
        start = time.time()
        try:
            result = run_workflow(f"test query {i}", enable_telemetry=True)
            elapsed_ms = (time.time() - start) * 1000
            results["runs"].append({
                "iteration": i,
                "success": True,
                "latency_ms": elapsed_ms,
                "response": result.get("response", "")[:50],
            })
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            results["runs"].append({
                "iteration": i,
                "success": False,
                "latency_ms": elapsed_ms,
                "error": str(e),
            })

        if (i + 1) % 10 == 0:
            _, peak = tracemalloc.get_traced_memory()
            print(f"  Iteration {i+1}/{num_iterations}: peak memory = {peak:,} bytes")

    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results["peak_memory_bytes"] = peak_memory
    results["successful_requests"] = sum(1 for r in results["runs"] if r["success"])
    results["failed_requests"] = sum(1 for r in results["runs"] if not r["success"])
    results["status"] = "executed"

    shutdown_telemetry()
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 02: Backend Failure")
    print("=" * 60)
    print()
    print("Methodology:")
    print("  - OTLP endpoint: http://localhost:9999 (dead)")
    print("  - Bounded queue: 100 spans")
    print("  - Run workflow repeatedly with telemetry enabled")
    print("  - Observe: application success, memory growth, errors")
    print()

    results = run_experiment(num_iterations=20)

    print()
    print("Results (label: synthetic workload):")
    print(f"  Successful requests: {results['successful_requests']}/{results['iterations']}")
    print(f"  Failed requests: {results['failed_requests']}/{results['iterations']}")
    print(f"  Peak memory: {results['peak_memory_bytes']:,} bytes")
    print()
    if results["failed_requests"] == 0:
        print("  ✓ Fail-open: application continued despite backend being down")
    else:
        print("  ✗ Application failures detected — check fail-open policy")
    print()
    print("NOTE: These are synthetic workload measurements from a mock lab.")