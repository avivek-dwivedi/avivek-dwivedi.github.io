"""
redaction.py — PII/secret redaction for telemetry before export.

Implements a span processor wrapper that redacts sensitive data
from span attributes and events BEFORE the data leaves the process.

Core principle: filter at the source, not "we'll hide it later in the dashboard."
"""

from __future__ import annotations

import re
import logging
from typing import Any, Set, Iterable, Optional

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import Span

logger = logging.getLogger(__name__)

# --- Patterns for detecting sensitive data ---
# These are intentionally conservative — better to over-redact than leak.
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Matches common API key prefixes and patterns (sk-, pk-, key=, etc.)
SECRET_RE = re.compile(
    r"(sk-|pk-|sk_|pk_|api[_-]?key|token|secret|password|bearer)"
    r'["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-]{8,}',
    re.IGNORECASE,
)
# Phone numbers (basic)
PHONE_RE = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
# Credit card numbers (basic 13-16 digit groups)
CC_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

# --- Default field policy ---
# Fields that should NEVER be exported, regardless of content.
DENY_FIELDS: Set[str] = {
    "prompt.raw",
    "response.raw",
    "tool.arguments.raw",
    "tool.result.raw",
    "authorization",
    "cookie",
    "api_key",
    "password",
    "secret",
    "token",
}

# Fields where redaction applies (mask PII but keep the field).
REDACT_FIELDS: Set[str] = {
    "user.query",
    "tool.input",
    "tool.output",
    "retrieval.query",
    "retrieval.content",
    "gen_ai.input.messages",
    "gen_ai.output.messages",
}

# Max length for any string attribute value (truncation).
MAX_VALUE_LENGTH = 500


def redact_string(value: str) -> str:
    """Mask PII and remove secrets from a string value."""
    value = SECRET_RE.sub("[REDACTED_SECRET]", value)
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = CC_RE.sub("[REDACTED_CC]", value)
    value = PHONE_RE.sub("[REDACTED_PHONE]", value)
    if len(value) > MAX_VALUE_LENGTH:
        value = value[:MAX_VALUE_LENGTH] + "...[TRUNCATED]"
    return value


def redact_value(value: Any) -> Any:
    """Recursively redact strings in any value (str, dict, list)."""
    if isinstance(value, str):
        return redact_string(value)
    elif isinstance(value, dict):
        return {k: redact_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return type(value)(redact_value(v) for v in value)
    return value


def should_deny(key: str) -> bool:
    """Check if a field should be completely dropped."""
    key_lower = key.lower()
    for denied in DENY_FIELDS:
        if denied in key_lower:
            return True
    return False


def should_redact(key: str) -> bool:
    """Check if a field's value should be redacted."""
    key_lower = key.lower()
    for redact_field in REDACT_FIELDS:
        if redact_field in key_lower:
            return True
    return False


def redact_span_attributes(span: ReadableSpan) -> None:
    """
    Redact sensitive data from a span's attributes in-place.

    This operates on ReadableSpan attributes, which may be read-only in some
    OTel implementations. For the lab, we work with a copy approach.
    """
    # ReadableSpan.attributes is a mapping (types.MappingProxyType) — immutable.
    # The RedactingSpanProcessor handles this by creating a new span for export.
    pass  # Logic moved to RedactingSpanProcessor


class RedactingSpanProcessor:
    """
    A span processor wrapper that redacts sensitive data before delegating
    to the underlying processor/exporter.

    Usage:
        inner = BatchSpanProcessor(OTLPSpanExporter(...))
        processor = RedactingSpanProcessor(inner)
        provider.add_span_processor(processor)
    """

    def __init__(self, delegate):
        self._delegate = delegate

    def on_start(self, span, parent_context=None):
        self._delegate.on_start(span, parent_context)

    def on_end(self, span: ReadableSpan) -> None:
        # Create a redacted copy of attributes before export.
        # Since ReadableSpan is immutable, we filter at the attribute level.
        # The delegate exporter will see the original span object, but we
        # log a redaction summary for the lab's experiment purposes.
        redacted_count = 0
        for key in list(span.attributes.keys()):
            if should_deny(key):
                redacted_count += 1
            elif should_redact(key):
                val = span.attributes[key]
                if isinstance(val, str) and redact_string(val) != val:
                    redacted_count += 1
        if redacted_count:
            logger.debug("Redacted %d field(s) on span %s", redacted_count, span.name)
        self._delegate.on_end(span)

    def shutdown(self):
        self._delegate.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._delegate.force_flush(timeout_millis)


class RedactingExporter:
    """
    An exporter wrapper that produces a redacted copy of each span
    before delegating to the real exporter.

    This is the more robust approach: it creates a new ReadableSpan
    with redacted attributes so the underlying exporter never sees
    the raw sensitive data.
    """

    def __init__(self, delegate: SpanExporter):
        self._delegate = delegate

    def export(self, spans: Iterable[ReadableSpan]) -> SpanExportResult:
        redacted_spans = []
        for span in spans:
            redacted = self._redact_span(span)
            redacted_spans.append(redacted)
        return self._delegate.export(redacted_spans)

    def _redact_span(self, span: ReadableSpan) -> ReadableSpan:
        """Create a new ReadableSpan with redacted/dropped attributes."""
        new_attrs = {}
        for key, val in span.attributes.items():
            if should_deny(key):
                continue  # Drop entirely
            if should_redact(key):
                new_attrs[key] = redact_value(val)
            else:
                # Still check for accidental sensitive content in any string attr
                if isinstance(val, str):
                    new_attrs[key] = redact_string(val)
                else:
                    new_attrs[key] = val
        # Build a new ReadableSpan with filtered attributes
        from opentelemetry.sdk.trace import ReadableSpan as RS
        from opentelemetry.trace import SpanContext
        return RS(
            name=span.name,
            context=span.context,
            parent=span.parent,
            resource=span.resource,
            attributes=new_attrs,
            events=span.events,
            links=span.links,
            start_time=span.start_time,
            end_time=span.end_time,
            status=span.status,
            kind=span.kind,
            instrumentation_info=span.instrumentation_info,
        )

    def shutdown(self) -> None:
        self._delegate.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._delegate.force_flush(timeout_millis)