"""
sampling.py — Head and tail sampling policies for LLM telemetry.

Head sampling: decision made at trace start (before outcome known).
Tail sampling: decision made after trace completes (can retain failures, slow traces).

The lab demonstrates both concepts. Tail sampling requires the OTel Collector's
tail_sampling processor in production — the lab simulates the policy logic.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, Optional

from opentelemetry.trace import SpanContext
from opentelemetry.trace.status import Status, StatusCode


class HeadSampler:
    """
    Head sampling: decide at trace start whether to sample.

    Problem: does not yet know whether the request will be slow, expensive,
    failed, or interesting. May drop the most valuable traces.
    """

    def __init__(self, rate: float = 0.1):
        """
        Args:
            rate: Fraction of traces to keep (0.0 to 1.0).
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("rate must be between 0.0 and 1.0")
        self.rate = rate

    def should_sample(self, trace_id: int) -> bool:
        """Make a sampling decision based on trace_id alone."""
        # Deterministic based on trace_id hash for consistent decisions
        return (trace_id % 10000) / 10000.0 < self.rate

    def __repr__(self):
        return f"HeadSampler(rate={self.rate})"


class TailSamplingPolicy:
    """
    Tail sampling policy: decide AFTER seeing trace outcome.

    Can retain:
    - 100% of failed traces
    - 100% of traces above a latency threshold
    - 100% of selected critical workflows
    - 100% of high-token/cost traces
    - Sample normal successful traffic at a lower rate

    This is an example policy, not a universal rule.
    """

    def __init__(
        self,
        always_keep_errors: bool = True,
        latency_threshold_ms: float = 5000.0,
        always_keep_workflows: Optional[set] = None,
        normal_sample_rate: float = 0.1,
        high_token_threshold: int = 4000,
    ):
        self.always_keep_errors = always_keep_errors
        self.latency_threshold_ms = latency_threshold_ms
        self.always_keep_workflows = always_keep_workflows or set()
        self.normal_sample_rate = normal_sample_rate
        self.high_token_threshold = high_token_threshold

    def should_keep(
        self,
        status: StatusCode,
        duration_ms: float,
        workflow_name: str = "",
        total_tokens: int = 0,
        is_critical: bool = False,
    ) -> bool:
        """
        Decide whether to retain a completed trace.

        Args:
            status: The trace's final status code.
            duration_ms: Total trace duration in milliseconds.
            workflow_name: Name of the workflow.
            total_tokens: Total tokens consumed across all generations.
            is_critical: Whether this is a flagged critical workflow.

        Returns:
            True if the trace should be retained.
        """
        # 100% of failed traces
        if self.always_keep_errors and status == StatusCode.ERROR:
            return True

        # 100% of extremely slow traces
        if duration_ms >= self.latency_threshold_ms:
            return True

        # 100% of selected critical workflows
        if workflow_name in self.always_keep_workflows or is_critical:
            return True

        # 100% of high-token traces
        if total_tokens >= self.high_token_threshold:
            return True

        # Sample normal successful traffic
        return random.random() < self.normal_sample_rate

    def __repr__(self):
        return (
            f"TailSamplingPolicy(errors={self.always_keep_errors}, "
            f"latency_threshold={self.latency_threshold_ms}ms, "
            f"normal_rate={self.normal_sample_rate})"
        )