"""
Experiment 05 — Sampling

Question: Can we retain high-value failure traces while reducing normal telemetry volume?

Procedure:
  Generate synthetic workload: normal, slow, failed, high-cost traces
  Compare:
    A: Uniform head sampling (10%)
    B: Policy/tail-oriented retention (100% failures, 10% normal)

NOT EXECUTED. This script defines methodology.
Tail sampling in production requires the OTel Collector tail_sampling processor.
This lab simulates the policy logic.
"""

from __future__ import annotations

import random
from typing import Dict, Any, List

from opentelemetry.trace.status import StatusCode

from sampling import HeadSampler, TailSamplingPolicy


def generate_synthetic_workload(num_traces: int = 200) -> List[Dict[str, Any]]:
    """
    Generate a synthetic workload with a mix of trace types:
    - 70% normal successful traces
    - 10% failed traces
    - 10% slow traces (>5s)
    - 10% high-token traces (>4000 tokens)
    """
    traces = []
    for i in range(num_traces):
        r = random.random()
        if r < 0.10:
            # Failed trace
            traces.append({
                "trace_id": i,
                "status": StatusCode.ERROR,
                "duration_ms": random.uniform(500, 3000),
                "workflow": "support",
                "total_tokens": random.randint(200, 1000),
                "category": "failed",
            })
        elif r < 0.20:
            # Slow trace
            traces.append({
                "trace_id": i,
                "status": StatusCode.OK,
                "duration_ms": random.uniform(5000, 15000),
                "workflow": "support",
                "total_tokens": random.randint(500, 2000),
                "category": "slow",
            })
        elif r < 0.30:
            # High-token trace
            traces.append({
                "trace_id": i,
                "status": StatusCode.OK,
                "duration_ms": random.uniform(1000, 4000),
                "workflow": "support",
                "total_tokens": random.randint(4000, 8000),
                "category": "high_token",
            })
        else:
            # Normal successful trace
            traces.append({
                "trace_id": i,
                "status": StatusCode.OK,
                "duration_ms": random.uniform(200, 2000),
                "workflow": "support",
                "total_tokens": random.randint(200, 1500),
                "category": "normal",
            })
    return traces


def run_experiment(num_traces: int = 200) -> Dict[str, Any]:
    """Run the sampling comparison experiment."""
    results: Dict[str, Any] = {
        "experiment": "sampling",
        "num_traces": num_traces,
        "status": "not_executed",
    }

    workload = generate_synthetic_workload(num_traces)

    # --- Run A: Head sampling (10%) ---
    head_sampler = HeadSampler(rate=0.10)
    head_kept = [t for t in workload if head_sampler.should_sample(t["trace_id"])]
    head_kept_failures = sum(1 for t in head_kept if t["category"] == "failed")
    head_kept_slow = sum(1 for t in head_kept if t["category"] == "slow")
    head_kept_high_token = sum(1 for t in head_kept if t["category"] == "high_token")

    # --- Run B: Tail sampling policy ---
    tail_policy = TailSamplingPolicy(
        always_keep_errors=True,
        latency_threshold_ms=5000.0,
        normal_sample_rate=0.10,
        high_token_threshold=4000,
    )
    tail_kept = [
        t for t in workload
        if tail_policy.should_keep(
            status=t["status"],
            duration_ms=t["duration_ms"],
            workflow_name=t["workflow"],
            total_tokens=t["total_tokens"],
        )
    ]
    tail_kept_failures = sum(1 for t in tail_kept if t["category"] == "failed")
    tail_kept_slow = sum(1 for t in tail_kept if t["category"] == "slow")
    tail_kept_high_token = sum(1 for t in tail_kept if t["category"] == "high_token")

    total_failures = sum(1 for t in workload if t["category"] == "failed")
    total_slow = sum(1 for t in workload if t["category"] == "slow")
    total_high_token = sum(1 for t in workload if t["category"] == "high_token")

    results["head_sampling"] = {
        "total_kept": len(head_kept),
        "retention_rate": len(head_kept) / num_traces,
        "failures_retained": head_kept_failures,
        "failures_retention_rate": head_kept_failures / total_failures if total_failures else 0,
        "slow_retained": head_kept_slow,
        "slow_retention_rate": head_kept_slow / total_slow if total_slow else 0,
        "high_token_retained": head_kept_high_token,
    }
    results["tail_sampling"] = {
        "total_kept": len(tail_kept),
        "retention_rate": len(tail_kept) / num_traces,
        "failures_retained": tail_kept_failures,
        "failures_retention_rate": tail_kept_failures / total_failures if total_failures else 0,
        "slow_retained": tail_kept_slow,
        "slow_retention_rate": tail_kept_slow / total_slow if total_slow else 0,
        "high_token_retained": tail_kept_high_token,
    }
    results["total_failures"] = total_failures
    results["total_slow"] = total_slow
    results["total_high_token"] = total_high_token
    results["status"] = "executed"

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 05: Sampling")
    print("=" * 60)
    print()
    print("Methodology:")
    print("  A: Head sampling (10% uniform)")
    print("  B: Tail sampling policy (100% errors, 100% slow, 10% normal)")
    print("  Workload: 70% normal, 10% failed, 10% slow, 10% high-token")
    print()

    results = run_experiment(num_traces=200)

    print("Results (label: synthetic workload):")
    print()
    print(f"  Total traces: {results['num_traces']}")
    print(f"  Failures in workload: {results['total_failures']}")
    print(f"  Slow traces: {results['total_slow']}")
    print(f"  High-token traces: {results['total_high_token']}")
    print()
    h = results["head_sampling"]
    t = results["tail_sampling"]
    print(f"  Head sampling (10%):")
    print(f"    Retained: {h['total_kept']} ({h['retention_rate']:.1%})")
    print(f"    Failures retained: {h['failures_retained']}/{results['total_failures']} ({h['failures_retention_rate']:.1%})")
    print(f"    Slow retained: {h['slow_retained']}/{results['total_slow']} ({h['slow_retention_rate']:.1%})")
    print()
    print(f"  Tail sampling policy:")
    print(f"    Retained: {t['total_kept']} ({t['retention_rate']:.1%})")
    print(f"    Failures retained: {t['failures_retained']}/{results['total_failures']} ({t['failures_retention_rate']:.1%})")
    print(f"    Slow retained: {t['slow_retained']}/{results['total_slow']} ({t['slow_retention_rate']:.1%})")
    print()
    print("  Key insight: tail sampling retains 100% of failures while")
    print("  head sampling randomly drops failures at the same rate as normal traffic.")