"""
services/agent_b.py — Validation agent service (separate process for propagation tests).

Receives trace context from upstream callers via W3C Trace Context headers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from pydantic import BaseModel

from telemetry import init_telemetry, shutdown_telemetry
from tracing import extract_trace_context, agent_span, tool_span
from tools import execute_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_telemetry(enable_otlp=True, enable_console=False)

app = FastAPI(title="Agent B — Validation", version="0.1.0")


class ValidationRequest(BaseModel):
    response: str


@app.on_event("shutdown")
def _shutdown():
    shutdown_telemetry()


@app.post("/validate")
async def validate(req: ValidationRequest, request: Request):
    """Validation endpoint — extracts trace context from incoming headers."""
    incoming = dict(request.headers)
    context = extract_trace_context(incoming)

    with agent_span("validation_agent", "1.5.0"):
        with tool_span("validate.response"):
            result = execute_tool("validate.response", response=req.response)

        return {
            "valid": result["valid"],
            "score": result["score"],
        }