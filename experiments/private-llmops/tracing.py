"""
tracing.py — Span helpers and context propagation utilities.

Provides:
- Context manager helpers for creating nested spans (workflow, agent, generation, tool, retrieval)
- W3C Trace Context injection/extraction for cross-service propagation
- Controlled attribute setting using OTel GenAI semantic conventions

GenAI attribute names follow the OpenTelemetry GenAI semantic conventions
(github.com/open-telemetry/semantic-conventions-genai, Development stability, September 2026).
Application-specific attributes (workflow.*, agent.*) are clearly non-standard.
"""

from __future__ import annotations

import contextlib
from typing import Any, Dict, Iterator, Optional

from opentelemetry import trace
from opentelemetry.trace import Span
from opentelemetry.propagate import inject, extract

# --- OTel GenAI semantic convention attributes (Development stability) ---
# Verified against github.com/open-telemetry/semantic-conventions-genai (Sep 2026).
# These are standard names — do not modify.
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_PROVIDER_NAME = "gen_ai.provider.name"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_USAGE_CACHE_READ_INPUT_TOKENS = "gen_ai.usage.cache_read.input_tokens"
GEN_AI_USAGE_REASONING_OUTPUT_TOKENS = "gen_ai.usage.reasoning.output_tokens"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"
GEN_AI_TOOL_CALL_ID = "gen_ai.tool.call.id"
GEN_AI_TOOL_DESCRIPTION = "gen_ai.tool.description"
GEN_AI_TOOL_TYPE = "gen_ai.tool.type"
GEN_AI_AGENT_NAME = "gen_ai.agent.name"
GEN_AI_AGENT_VERSION = "gen_ai.agent.version"
GEN_AI_CONVERSATION_ID = "gen_ai.conversation.id"

# --- Application-specific attributes (clearly non-standard) ---
WORKFLOW_NAME = "workflow.name"
WORKFLOW_VERSION = "workflow.version"
AGENT_NAME = "agent.name"
AGENT_VERSION = "agent.version"
INTERNAL_REQUEST_ID = "internal_request_id"
SESSION_ID = "session.id"
TENANT_ID = "tenant.id"


@contextlib.contextmanager
def workflow_span(name: str, version: str = "", request_id: str = "",
                  session_id: str = "", tenant_id: str = "") -> Iterator[Span]:
    """Create a root workflow span with controlled attributes."""
    tracer = trace.get_tracer("multi-agent")
    with tracer.start_as_current_span(f"workflow.{name}") as span:
        span.set_attribute(WORKFLOW_NAME, name)
        if version:
            span.set_attribute(WORKFLOW_VERSION, version)
        if request_id:
            span.set_attribute(INTERNAL_REQUEST_ID, request_id)
        if session_id:
            span.set_attribute(SESSION_ID, session_id)
        if tenant_id:
            span.set_attribute(TENANT_ID, tenant_id)
        yield span


@contextlib.contextmanager
def agent_span(name: str, version: str = "") -> Iterator[Span]:
    """Create an agent span — child of whatever span is currently active."""
    tracer = trace.get_tracer("multi-agent")
    with tracer.start_as_current_span(f"agent.{name}") as span:
        span.set_attribute(AGENT_NAME, name)
        span.set_attribute(GEN_AI_AGENT_NAME, name)
        if version:
            span.set_attribute(AGENT_VERSION, version)
            span.set_attribute(GEN_AI_AGENT_VERSION, version)
        yield span


@contextlib.contextmanager
def generation_span(model: str, provider: str = "mock",
                    operation: str = "chat") -> Iterator[Span]:
    """Create a GenAI generation span with standard semantic conventions."""
    tracer = trace.get_tracer("multi-agent")
    span_name = f"{operation} {model}"
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute(GEN_AI_OPERATION_NAME, operation)
        span.set_attribute(GEN_AI_PROVIDER_NAME, provider)
        span.set_attribute(GEN_AI_REQUEST_MODEL, model)
        yield span


def set_token_usage(span: Span, input_tokens: int, output_tokens: int,
                    cached_tokens: int = 0, reasoning_tokens: int = 0):
    """Set token usage attributes on a generation span."""
    span.set_attribute(GEN_AI_USAGE_INPUT_TOKENS, input_tokens)
    span.set_attribute(GEN_AI_USAGE_OUTPUT_TOKENS, output_tokens)
    if cached_tokens:
        span.set_attribute(GEN_AI_USAGE_CACHE_READ_INPUT_TOKENS, cached_tokens)
    if reasoning_tokens:
        span.set_attribute(GEN_AI_USAGE_REASONING_OUTPUT_TOKENS, reasoning_tokens)


@contextlib.contextmanager
def tool_span(tool_name: str, tool_call_id: str = "",
              tool_type: str = "function") -> Iterator[Span]:
    """Create a tool execution span — distinguishable from surrounding LLM generation."""
    tracer = trace.get_tracer("multi-agent")
    with tracer.start_as_current_span(f"tool.{tool_name}") as span:
        span.set_attribute(GEN_AI_OPERATION_NAME, "execute_tool")
        span.set_attribute(GEN_AI_TOOL_NAME, tool_name)
        span.set_attribute(GEN_AI_TOOL_TYPE, tool_type)
        if tool_call_id:
            span.set_attribute(GEN_AI_TOOL_CALL_ID, tool_call_id)
        yield span


@contextlib.contextmanager
def retrieval_span(retriever_version: str = "1.0.0") -> Iterator[Span]:
    """Create a retrieval span for RAG operations."""
    tracer = trace.get_tracer("multi-agent")
    with tracer.start_as_current_span("retrieval") as span:
        span.set_attribute("retrieval.type", "vector")
        span.set_attribute("retrieval.version", retriever_version)
        yield span


@contextlib.contextmanager
def handoff_span(source_agent: str, target_agent: str,
                 handoff_type: str = "delegation") -> Iterator[Span]:
    """
    Create a handoff span recording agent-to-agent transfer.

    Records observable handoff metadata only.
    Does NOT log internal reasoning or chain-of-thought.
    """
    tracer = trace.get_tracer("multi-agent")
    with tracer.start_as_current_span(f"handoff.{source_agent}_to_{target_agent}") as span:
        span.set_attribute("handoff.source_agent", source_agent)
        span.set_attribute("handoff.target_agent", target_agent)
        span.set_attribute("handoff.type", handoff_type)
        yield span


# --- Cross-service context propagation (W3C Trace Context) ---

def inject_trace_context(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Inject W3C trace context into HTTP headers for cross-service propagation.

    The traceparent header carries trace-id and parent-span-id so downstream
    services can create child spans under the same trace.
    """
    if headers is None:
        headers = {}
    inject(headers)
    return headers


def extract_trace_context(headers: Dict[str, str]) -> Any:
    """
    Extract W3C trace context from incoming HTTP headers.

    Returns an OTel Context that can be used as the parent for new spans,
    connecting this service's spans to the upstream trace.
    """
    return extract(headers)