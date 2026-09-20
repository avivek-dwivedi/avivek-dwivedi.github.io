"""
mcp/server.py — MCP server with trace context extraction.

Receives W3C Trace Context from the MCP client and creates child spans
under the caller's trace, so tool execution appears inside the workflow trace.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from pydantic import BaseModel

from telemetry import init_telemetry, shutdown_telemetry
from tracing import extract_trace_context, tool_span
from tools import execute_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_telemetry(enable_otlp=True, enable_console=False)

app = FastAPI(title="MCP Server", version="0.1.0")


@app.on_event("shutdown")
def _shutdown():
    shutdown_telemetry()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """
    Execute a tool on the MCP server.

    Extracts trace context from incoming headers so this span
    joins the caller's trace (W3C Trace Context propagation).
    """
    import json
    body = await request.json()
    incoming = dict(request.headers)
    context = extract_trace_context(incoming)

    # Map URL tool names to registered tools
    tool_map = {
        "lookup_order": "billing.lookup_order",
        "search": "kb.search",
        "validate": "validate.response",
    }

    registered_name = tool_map.get(tool_name, tool_name)
    with tool_span(registered_name, tool_type="mcp"):
        try:
            result = execute_tool(registered_name, **body)
            return {"status": "ok", "result": result}
        except Exception as e:
            logger.error("Tool execution failed: %s", e)
            return {"status": "error", "error": str(e)}