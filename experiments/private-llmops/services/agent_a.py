"""
services/agent_a.py — Research agent service (separate process for propagation tests).

This service runs independently and receives trace context via HTTP headers.
It demonstrates cross-service trace propagation: if the caller injects W3C
trace context, this service's spans join the caller's trace.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from pydantic import BaseModel

from telemetry import init_telemetry, shutdown_telemetry
from tracing import extract_trace_context, agent_span, generation_span, set_token_usage
from retrieval import retrieve
from tools import execute_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_telemetry(enable_otlp=True, enable_console=False)

app = FastAPI(title="Agent A — Research", version="0.1.0")


class ResearchRequest(BaseModel):
    query: str


@app.on_event("shutdown")
def _shutdown():
    shutdown_telemetry()


@app.post("/research")
async def research(req: ResearchRequest, request: Request):
    """Research endpoint — extracts trace context from incoming headers."""
    incoming = dict(request.headers)
    context = extract_trace_context(incoming)

    with agent_span("research_agent", "2.1.0"):
        # Retrieval
        docs = retrieve(req.query, top_k=5)

        # Tool
        results = execute_tool("kb.search", query=req.query, top_k=3)

        # Mock generation
        with generation_span(model="mock-gpt-4", provider="mock") as gen:
            import time, random
            time.sleep(random.uniform(0.3, 0.8))
            input_tokens = random.randint(100, 300)
            output_tokens = random.randint(50, 200)
            set_token_usage(gen, input_tokens, output_tokens)

        return {
            "docs": len(docs),
            "results": len(results),
            "tokens": {"input": input_tokens, "output": output_tokens},
        }