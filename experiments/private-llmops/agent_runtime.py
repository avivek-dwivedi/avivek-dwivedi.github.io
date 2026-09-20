"""
agent_runtime.py — Multi-agent workflow runtime with OpenTelemetry instrumentation.

Implements a synthetic multi-agent workflow:
    User request
    → Supervisor
    → Research Agent (retrieval + tool + mock generation)
    → Validation Agent
    → Final response

All model components are mock/fake. No real LLM API calls.
"""

from __future__ import annotations

import time
import random
import uuid
from typing import Any, Dict, List, Optional

from tracing import (
    workflow_span, agent_span, generation_span, tool_span,
    retrieval_span, handoff_span, set_token_usage,
)
from tools import execute_tool
from retrieval import retrieve
from evaluations import evaluate_trace

# --- Mock LLM generation ---

def mock_generate(model: str, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
    """
    Mock LLM generation — returns a synthetic response with simulated token usage.

    No real API call. Token counts are synthetic and clearly labeled.
    """
    time.sleep(random.uniform(0.3, 1.0))  # Simulate model latency
    input_tokens = len(prompt.split()) + random.randint(50, 200)
    output_tokens = random.randint(50, max_tokens)
    return {
        "text": f"[Synthetic response from {model}] Based on the available context, "
                f"here is a generated answer for the given query.",
        "model": model,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": random.randint(0, 20),
            "reasoning_tokens": random.randint(0, 30) if "reasoning" in model else 0,
        },
        "latency_ms": random.uniform(300, 1000),
    }


# --- Agent implementations ---

def supervisor_agent(request: str) -> Dict[str, Any]:
    """Supervisor: routes the request to the appropriate agents."""
    with agent_span("supervisor", "1.0.0"):
        time.sleep(random.uniform(0.05, 0.15))
        return {"plan": "research + validate", "request": request}


def research_agent(query: str) -> Dict[str, Any]:
    """Research agent: retrieval + tool + LLM generation."""
    with agent_span("research_agent", "2.1.0"):
        # Retrieval
        with retrieval_span(retriever_version="1.0.0"):
            docs = retrieve(query, top_k=5)

        # Tool call
        with tool_span("kb.search", tool_call_id=str(uuid.uuid4())):
            search_results = execute_tool("kb.search", query=query, top_k=3)

        # LLM generation
        with generation_span(model="mock-gpt-4", provider="mock") as gen_span:
            result = mock_generate("mock-gpt-4", query)
            set_token_usage(
                gen_span,
                input_tokens=result["usage"]["input_tokens"],
                output_tokens=result["usage"]["output_tokens"],
                cached_tokens=result["usage"]["cached_tokens"],
                reasoning_tokens=result["usage"]["reasoning_tokens"],
            )

        return {
            "answer": result["text"],
            "retrieved_docs": len(docs),
            "search_results": len(search_results),
            "tokens": result["usage"],
        }


def validation_agent(response: str) -> Dict[str, Any]:
    """Validation agent: checks the research agent's output."""
    with agent_span("validation_agent", "1.5.0"):
        # Tool call
        with tool_span("validate.response", tool_call_id=str(uuid.uuid4())):
            validation = execute_tool("validate.response", response=response)

        # LLM generation (brief)
        with generation_span(model="mock-gpt-4-mini", provider="mock") as gen_span:
            result = mock_generate("mock-gpt-4-mini", f"Validate: {response}", max_tokens=50)
            set_token_usage(
                gen_span,
                input_tokens=result["usage"]["input_tokens"],
                output_tokens=result["usage"]["output_tokens"],
            )

        return {"valid": validation["valid"], "score": validation["score"]}


# --- Full workflow ---

def run_workflow(user_request: str, request_id: str = "",
                 session_id: str = "", tenant_id: str = "",
                 enable_telemetry: bool = True) -> Dict[str, Any]:
    """
    Run the full multi-agent workflow with end-to-end tracing.

    Args:
        user_request: The user's input query.
        request_id: Internal request ID for correlation.
        session_id: Session ID for trace grouping.
        tenant_id: Tenant ID for multi-tenant attribution.
        enable_telemetry: If False, run without instrumentation (for overhead experiments).

    Returns:
        Workflow result with latency and token metadata.
    """
    start = time.time()

    if not request_id:
        request_id = str(uuid.uuid4())

    def _run_inner() -> Dict[str, Any]:
        # Supervisor
        plan = supervisor_agent(user_request)

        # Handoff: supervisor → research
        with handoff_span("supervisor", "research_agent"):
            pass  # Observable handoff event only

        # Research
        research_result = research_agent(user_request)

        # Handoff: research → validation
        with handoff_span("research_agent", "validation_agent"):
            pass

        # Validation
        validation = validation_agent(research_result["answer"])

        # Final generation
        with generation_span(model="mock-gpt-4", provider="mock") as gen_span:
            final = mock_generate("mock-gpt-4", research_result["answer"], max_tokens=100)
            set_token_usage(
                gen_span,
                input_tokens=final["usage"]["input_tokens"],
                output_tokens=final["usage"]["output_tokens"],
            )

        total_tokens = (
            research_result["tokens"]["input_tokens"]
            + research_result["tokens"]["output_tokens"]
            + final["usage"]["input_tokens"]
            + final["usage"]["output_tokens"]
        )

        return {
            "request_id": request_id,
            "response": final["text"],
            "valid": validation["valid"],
            "validation_score": validation["score"],
            "total_tokens": total_tokens,
            "duration_ms": (time.time() - start) * 1000,
        }

    if enable_telemetry:
        with workflow_span("support", version="1.2.0", request_id=request_id,
                           session_id=session_id, tenant_id=tenant_id):
            result = _run_inner()
    else:
        result = _run_inner()

    result["duration_ms"] = (time.time() - start) * 1000
    return result