"""
tools.py — Mock tool implementations for the multi-agent workflow.

Tools are fake/synthetic — no real external dependencies.
Each tool returns a deterministic result and simulates latency.
"""

from __future__ import annotations

import time
import random
from typing import Any, Dict


def lookup_order(order_id: str) -> Dict[str, Any]:
    """
    Mock billing tool: look up an order by ID.

    Simulates a database query with ~50-200ms latency.
    Does NOT log real customer data — returns synthetic data only.
    """
    time.sleep(random.uniform(0.05, 0.20))
    return {
        "order_id": order_id,
        "status": "shipped",
        "total": "$129.99",
        "tracking": "TRK" + str(random.randint(100000, 999999)),
    }


def search_kb(query: str, top_k: int = 5) -> list:
    """
    Mock knowledge base search tool.

    Simulates an external search API with variable latency (0.5-2.0s).
    This is the tool that dominated latency in the illustrative trace.
    """
    time.sleep(random.uniform(0.5, 2.0))
    return [
        {"doc_id": f"DOC-{i}", "title": f"Result {i}", "snippet": "Synthetic content..."}
        for i in range(min(top_k, 5))
    ]


def validate_response(response: str, criteria: str = "default") -> Dict[str, Any]:
    """
    Mock validation tool: check a response against criteria.

    Simulates a validation check with ~200-500ms latency.
    """
    time.sleep(random.uniform(0.2, 0.5))
    return {
        "valid": True,
        "score": random.uniform(0.75, 0.98),
        "issues": [],
    }


TOOL_REGISTRY = {
    "billing.lookup_order": lookup_order,
    "kb.search": search_kb,
    "validate.response": validate_response,
}


def execute_tool(tool_name: str, **kwargs) -> Any:
    """Execute a registered tool by name."""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_REGISTRY[tool_name](**kwargs)