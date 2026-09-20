"""
Experiment 04 — Telemetry Volume

Question: How much storage does full-content vs metadata-only telemetry consume?

Procedure:
  A: Full prompt, full response, tool input/output, retrieval payload
  B: Metadata, IDs, controlled excerpts, redaction, truncation

Measure: bytes/event, bytes/trace, storage estimate, export latency, memory

NOT EXECUTED. This script defines methodology.
"""

from __future__ import annotations

import json
import sys
from typing import Dict, Any, List


def simulate_full_content_trace() -> Dict[str, Any]:
    """
    Simulate a Level 3 trace: full prompts, responses, tool args, retrieval content.
    """
    return {
        "trace_id": "abc123def456abc123def456abc123de",
        "workflow": "support",
        "spans": [
            {
                "name": "planner_agent",
                "attributes": {
                    "agent.name": "planner",
                    "gen_ai.input.messages": [
                        {"role": "system", "content": "You are a helpful support agent. " * 50},
                        {"role": "user", "content": "My order 198271 hasn't arrived. " * 10},
                    ],
                    "gen_ai.output.messages": [
                        {"role": "assistant", "content": "I'll help you with your order. " * 20},
                    ],
                    "gen_ai.usage.input_tokens": 850,
                    "gen_ai.usage.output_tokens": 200,
                },
            },
            {
                "name": "retrieval",
                "attributes": {
                    "retrieval.query": "order 198271 status shipping",
                    "retrieval.results": [
                        {"doc_id": "DOC-1", "content": "Shipping policy: all orders ship within 3-5 business days. " * 5},
                        {"doc_id": "DOC-2", "content": "Order tracking information and delivery policies. " * 5},
                        {"doc_id": "DOC-3", "content": "Return policy for undelivered items. " * 5},
                    ],
                },
            },
            {
                "name": "tool.billing.lookup_order",
                "attributes": {
                    "gen_ai.tool.name": "lookup_order",
                    "tool.input": {"order_id": "198271", "customer_email": "john@example.com"},
                    "tool.output": {
                        "order_id": "198271",
                        "status": "shipped",
                        "customer_name": "John Smith",
                        "customer_email": "john@example.com",
                        "shipping_address": "123 Main St, Springfield, IL 62701",
                        "tracking": "TRK987654",
                        "total": "$129.99",
                    },
                },
            },
            {
                "name": "final_generation",
                "attributes": {
                    "gen_ai.input.messages": [
                        {"role": "user", "content": "My order hasn't arrived. " * 10},
                        {"role": "system", "content": "Based on retrieval and tool results. " * 10},
                    ],
                    "gen_ai.output.messages": [
                        {"role": "assistant", "content": "Your order 198271 has been shipped. " * 15},
                    ],
                    "gen_ai.usage.input_tokens": 1200,
                    "gen_ai.usage.output_tokens": 350,
                },
            },
        ],
    }


def simulate_metadata_only_trace() -> Dict[str, Any]:
    """
    Simulate a Level 1-2 trace: metadata, IDs, controlled excerpts, redaction.
    No full prompts, responses, or tool arguments.
    """
    return {
        "trace_id": "abc123def456abc123def456abc123de",
        "workflow": "support",
        "spans": [
            {
                "name": "planner_agent",
                "attributes": {
                    "agent.name": "planner",
                    "gen_ai.operation.name": "chat",
                    "gen_ai.request.model": "mock-gpt-4",
                    "gen_ai.usage.input_tokens": 850,
                    "gen_ai.usage.output_tokens": 200,
                    # NO gen_ai.input.messages or gen_ai.output.messages
                },
            },
            {
                "name": "retrieval",
                "attributes": {
                    "retrieval.type": "vector",
                    "retrieval.top_k": 3,
                    "retrieval.doc_ids": ["DOC-1", "DOC-2", "DOC-3"],
                    "retrieval.scores": [0.92, 0.85, 0.71],
                    # NO retrieval.content or retrieval.query
                },
            },
            {
                "name": "tool.billing.lookup_order",
                "attributes": {
                    "gen_ai.tool.name": "lookup_order",
                    "gen_ai.tool.call.id": "call_mszuSIzqtI65i1wAUOE8w5H4",
                    "tool.status": "ok",
                    "tool.duration_ms": 150.0,
                    # NO tool.input or tool.output
                },
            },
            {
                "name": "final_generation",
                "attributes": {
                    "gen_ai.operation.name": "chat",
                    "gen_ai.request.model": "mock-gpt-4",
                    "gen_ai.usage.input_tokens": 1200,
                    "gen_ai.usage.output_tokens": 350,
                },
            },
        ],
    }


def run_experiment(num_traces: int = 100) -> Dict[str, Any]:
    """Run the telemetry volume comparison."""
    results: Dict[str, Any] = {
        "experiment": "telemetry_volume",
        "num_traces": num_traces,
        "status": "not_executed",
    }

    # Generate traces
    full_traces = [simulate_full_content_trace() for _ in range(num_traces)]
    metadata_traces = [simulate_metadata_only_trace() for _ in range(num_traces)]

    # Measure bytes
    full_bytes = sum(len(json.dumps(t).encode("utf-8")) for t in full_traces)
    metadata_bytes = sum(len(json.dumps(t).encode("utf-8")) for t in metadata_traces)

    results["full_content_bytes_per_trace"] = full_bytes / num_traces
    results["metadata_only_bytes_per_trace"] = metadata_bytes / num_traces
    results["full_content_total_bytes"] = full_bytes
    results["metadata_only_total_bytes"] = metadata_bytes
    results["reduction_ratio"] = full_bytes / metadata_bytes if metadata_bytes > 0 else 0
    results["status"] = "executed"

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("Experiment 04: Telemetry Volume")
    print("=" * 60)
    print()
    print("Methodology:")
    print("  A: Full prompt + response + tool args + retrieval content")
    print("  B: Metadata + IDs + controlled excerpts + redaction")
    print()

    results = run_experiment(num_traces=100)

    print("Results (label: synthetic workload):")
    print(f"  Full content: {results['full_content_bytes_per_trace']:.0f} bytes/trace")
    print(f"  Metadata only: {results['metadata_only_bytes_per_trace']:.0f} bytes/trace")
    print(f"  Reduction ratio: {results['reduction_ratio']:.1f}x")
    print(f"  Full content (100 traces): {results['full_content_total_bytes']:,} bytes")
    print(f"  Metadata only (100 traces): {results['metadata_only_total_bytes']:,} bytes")
    print()
    print("NOTE: Synthetic data. No real PII/secrets used.")
    print("Storage estimates extrapolate from these byte counts.")