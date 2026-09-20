"""
Experiment 03 — Trace Context Propagation

Question: Does trace context propagate across service and MCP boundaries?

Procedure:
  A: Without propagation at one boundary → observe fragmented traces
  B: With proper W3C trace context propagation → observe single connected trace

Architecture:
  FastAPI → Supervisor → Agent service (agent_a) → MCP → Tool

NOT EXECUTED. This script defines methodology.
Requires running agent_a and mcp/server as separate processes.

Running:
  # Terminal 1: Start MCP server
  python -m mcp.server

  # Terminal 2: Start agent_a service
  uvicorn services.agent_a:app --port 8011

  # Terminal 3: Run this experiment
  python -m experiments.context_propagation
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any

from tracing import inject_trace_context, workflow_span, agent_span


async def run_with_propagation() -> Dict[str, Any]:
    """
    Run A: Call agent_a service WITH trace context propagation.
    The downstream service should create child spans under this trace.
    """
    import httpx

    results = {"test": "with_propagation", "status": "not_executed"}

    with workflow_span("propagation_test", version="1.0.0", request_id="prop-test-001"):
        headers = {"Content-Type": "application/json"}
        headers = inject_trace_context(headers)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://localhost:8011/research",
                    json={"query": "test propagation"},
                    headers=headers,
                    timeout=10.0,
                )
                results["response_status"] = resp.status_code
                results["response_body"] = resp.json()
                results["status"] = "executed"
        except httpx.ConnectError:
            results["error"] = "agent_a service not running (start with: uvicorn services.agent_a:app --port 8011)"
        except Exception as e:
            results["error"] = str(e)

    return results


async def run_without_propagation() -> Dict[str, Any]:
    """
    Run B: Call agent_a service WITHOUT trace context propagation.
    The downstream service should create a SEPARATE, disconnected trace.
    """
    import httpx

    results = {"test": "without_propagation", "status": "not_executed"}

    with workflow_span("no_propagation_test", version="1.0.0", request_id="no-prop-001"):
        headers = {"Content-Type": "application/json"}
        # NOTE: Do NOT call inject_trace_context — no traceparent header

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "http://localhost:8011/research",
                    json={"query": "test no propagation"},
                    headers=headers,
                    timeout=10.0,
                )
                results["response_status"] = resp.status_code
                results["response_body"] = resp.json()
                results["status"] = "executed"
        except httpx.ConnectError:
            results["error"] = "agent_a service not running (start with: uvicorn services.agent_a:app --port 8011)"
        except Exception as e:
            results["error"] = str(e)

    return results


async def main():
    print("=" * 60)
    print("Experiment 03: Trace Context Propagation")
    print("=" * 60)
    print()
    print("Methodology:")
    print("  A: Call downstream service WITHOUT trace context → fragmented traces")
    print("  B: Call downstream service WITH W3C trace context → connected trace")
    print()
    print("Prerequisites:")
    print("  1. Start agent_a: uvicorn services.agent_a:app --port 8011")
    print("  2. Ensure OTLP exporter is configured (or console exporter for local)")
    print()

    print("Run A: Without propagation...")
    result_a = await run_without_propagation()
    print(f"  Result: {result_a.get('status', 'unknown')}")
    if "error" in result_a:
        print(f"  Error: {result_a['error']}")

    print()
    print("Run B: With propagation...")
    result_b = await run_with_propagation()
    print(f"  Result: {result_b.get('status', 'unknown')}")
    if "error" in result_b:
        print(f"  Error: {result_b['error']}")

    print()
    print("Expected:")
    print("  A: Two separate traces in the backend (disconnected)")
    print("  B: One connected trace with child spans from the downstream service")
    print()
    print("Verify by checking trace IDs in the backend or console output.")


if __name__ == "__main__":
    asyncio.run(main())