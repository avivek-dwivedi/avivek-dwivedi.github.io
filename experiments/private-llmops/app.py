"""
app.py — FastAPI entry point for the multi-agent workflow lab.

Exposes a POST /workflow endpoint that runs the synthetic multi-agent workflow
with full OpenTelemetry instrumentation.

Usage:
    python app.py
    # Then: curl -X POST http://localhost:8010/workflow -H "Content-Type: application/json" -d '{"query": "test"}'
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from pydantic import BaseModel

from telemetry import init_telemetry, shutdown_telemetry
from tracing import inject_trace_context, extract_trace_context, workflow_span
from agent_runtime import run_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize telemetry on startup
init_telemetry(enable_otlp=True, enable_console=False)

app = FastAPI(title="Private LLMOps Lab", version="0.1.0")


class WorkflowRequest(BaseModel):
    query: str
    session_id: str = ""
    tenant_id: str = ""


@app.on_event("shutdown")
def _shutdown():
    shutdown_telemetry()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/workflow")
async def workflow(req: WorkflowRequest, request: Request):
    """
    Run the multi-agent workflow.

    Extracts trace context from incoming headers (if present) so this
    service's spans join the caller's trace.
    """
    import uuid
    request_id = str(uuid.uuid4())

    # Extract incoming trace context for cross-service propagation
    incoming_headers = dict(request.headers)
    context = extract_trace_context(incoming_headers)

    result = run_workflow(
        user_request=req.query,
        request_id=request_id,
        session_id=req.session_id,
        tenant_id=req.tenant_id,
        enable_telemetry=True,
    )
    return result


@app.post("/workflow/propagate")
async def workflow_with_propagation(req: WorkflowRequest, request: Request):
    """
    Run workflow and inject trace context into a downstream call.

    Demonstrates trace context propagation across service boundaries.
    """
    import httpx
    import uuid

    request_id = str(uuid.uuid4())

    with workflow_span("propagated_workflow", request_id=request_id,
                       session_id=req.session_id):
        # Inject trace context into headers for downstream service
        headers = {"Content-Type": "application/json"}
        headers = inject_trace_context(headers)

        # Make a downstream call with propagated context
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "http://localhost:8010/workflow",
                    json={"query": req.query, "session_id": req.session_id},
                    headers=headers,
                    timeout=30.0,
                )
                return resp.json()
            except Exception as e:
                logger.error("Downstream call failed: %s", e)
                return {"error": str(e), "request_id": request_id}