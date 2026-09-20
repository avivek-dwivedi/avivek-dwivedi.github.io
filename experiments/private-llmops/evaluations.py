"""
evaluations.py — Score attachment to traces.

Demonstrates connecting evaluation scores to traces and observations.
Scores are synthetic for the lab — no real LLM-as-judge or human review.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional


# --- Score types ---
SCORE_TYPES = {
    "correctness": "Whether the response is factually correct (0.0-1.0)",
    "groundedness": "Whether the response is grounded in retrieved context (0.0-1.0)",
    "tool_correctness": "Whether the right tools were called with right args (0.0-1.0)",
    "trajectory_quality": "Quality of the agent execution path (0.0-1.0)",
    "policy_compliance": "Whether the response complies with policy (0.0-1.0)",
    "human_review": "Human reviewer score (0.0-1.0)",
}


def synthetic_score(score_type: str) -> float:
    """
    Generate a synthetic evaluation score.

    In production, this would be:
    - An LLM-as-judge call
    - A human review
    - A code-based evaluator
    - A rule-based check

    For the lab, returns a random score in a realistic range.
    """
    if score_type not in SCORE_TYPES:
        raise ValueError(f"Unknown score type: {score_type}. Valid: {list(SCORE_TYPES)}")
    return round(random.uniform(0.65, 0.98), 4)


def attach_score_to_trace(trace_id: str, score_type: str, score: float,
                          evaluator: str = "mock-evaluator",
                          evaluator_version: str = "0.1.0") -> Dict[str, Any]:
    """
    Attach an evaluation score to a trace.

    In Langfuse, this corresponds to creating a Score linked to a trace.
    In OTel, this can be a span event or a dedicated evaluation span.

    Returns a score record for the lab to log.
    """
    return {
        "trace_id": trace_id,
        "score_type": score_type,
        "score": score,
        "evaluator": evaluator,
        "evaluator_version": evaluator_version,
    }


def evaluate_trace(trace_id: str, response: str, retrieval_context: list = None,
                   tool_calls: list = None) -> list:
    """
    Run synthetic evaluations on a completed trace.

    Returns a list of score records.
    This simulates an offline evaluation pipeline.
    """
    scores = []

    # Correctness
    scores.append(attach_score_to_trace(trace_id, "correctness", synthetic_score("correctness")))

    # Groundedness (if retrieval was used)
    if retrieval_context:
        scores.append(attach_score_to_trace(trace_id, "groundedness", synthetic_score("groundedness")))

    # Tool correctness (if tools were called)
    if tool_calls:
        scores.append(attach_score_to_trace(trace_id, "tool_correctness", synthetic_score("tool_correctness")))

    # Trajectory quality
    scores.append(attach_score_to_trace(trace_id, "trajectory_quality", synthetic_score("trajectory_quality")))

    # Policy compliance
    scores.append(attach_score_to_trace(trace_id, "policy_compliance", synthetic_score("policy_compliance")))

    return scores