"""
telemetry.py — OpenTelemetry + Langfuse-compatible setup.

Configures the OTel SDK with:
- A console exporter (for local debugging)
- An OTLP exporter (for OTel Collector / Langfuse)
- Bounded batch span processor (async, not on critical path)
- Redaction processor (filters PII/secrets before export)

This module is the single place where telemetry backend configuration lives.
Applications import `get_tracer()` and `shutdown_telemetry()`.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from redaction import RedactingSpanProcessor

logger = logging.getLogger(__name__)

_tracer_provider: Optional[TracerProvider] = None
_initialized = False

# --- Configuration via environment ---
# Set OTEL_EXPORTER_OTLP_ENDPOINT to point to your OTel Collector or Langfuse OTLP endpoint.
# If unset, telemetry goes to console only (useful for local debugging).
OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "private-llmops-lab")
SERVICE_VERSION = os.environ.get("OTEL_SERVICE_VERSION", "0.1.0")
ENVIRONMENT = os.environ.get("OTEL_ENVIRONMENT", "development")

# Bounded queue: prevents unbounded memory growth if backend is slow/unavailable.
MAX_QUEUE_SIZE = int(os.environ.get("OTEL_BSP_MAX_QUEUE_SIZE", "2048"))
MAX_EXPORT_BATCH_SIZE = int(os.environ.get("OTEL_BSP_MAX_EXPORT_BATCH_SIZE", "512"))
EXPORT_TIMEOUT_MS = int(os.environ.get("OTEL_BSP_SCHEDULE_DELAY_MILLIS", "5000"))


def init_telemetry(enable_otlp: bool = True, enable_console: bool = False) -> TracerProvider:
    """
    Initialize the global TracerProvider with bounded async export and redaction.

    Args:
        enable_otlp: Export to OTLP endpoint (OTel Collector / Langfuse).
        enable_console: Also export to console (for local debugging).

    Returns:
        The TracerProvider (also set as global).
    """
    global _tracer_provider, _initialized

    if _initialized:
        return _tracer_provider  # type: ignore[return-value]

    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "service.version": SERVICE_VERSION,
            "deployment.environment": ENVIRONMENT,
        }
    )

    provider = TracerProvider(resource=resource)
    _tracer_provider = provider

    # Redaction wraps the actual exporter — secrets/PII filtered before leaving the process.
    if enable_console:
        console_processor = RedactingSpanProcessor(
            SimpleSpanProcessor(ConsoleSpanExporter())
        )
        provider.add_span_processor(console_processor)

    if enable_otlp and OTLP_ENDPOINT:
        otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT)
        # BatchSpanProcessor is async/bounded — does not block the application's critical path.
        batch_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=MAX_QUEUE_SIZE,
            max_export_batch_size=MAX_EXPORT_BATCH_SIZE,
            schedule_delay_millis=EXPORT_TIMEOUT_MS,
        )
        redacting_batch = RedactingSpanProcessor(batch_processor)
        provider.add_span_processor(redacting_batch)
        logger.info("OTLP export enabled: %s", OTLP_ENDPOINT)
    else:
        logger.info("OTLP export disabled (no OTEL_EXPORTER_OTLP_ENDPOINT set)")

    trace.set_tracer_provider(provider)
    _initialized = True
    return provider


def get_tracer(name: str = "multi-agent"):
    """Get a tracer instance. Initializes telemetry if not yet done."""
    if not _initialized:
        init_telemetry()
    return trace.get_tracer(name)


def shutdown_telemetry():
    """
    Gracefully flush all buffered telemetry and shut down.

    Must be called before process exit in short-lived scripts to avoid data loss.
    The BatchSpanProcessor's shutdown() flushes pending batches.
    """
    global _tracer_provider, _initialized
    if _tracer_provider:
        _tracer_provider.shutdown()
    _tracer_provider = None
    _initialized = False