"""
baselines.py — Baseline implementations for the adaptation evaluation lab.

Each baseline produces a prediction for an incident description.
Baselines use mock model responses — no real API calls.

The baselines simulate different non-training interventions:
- A: Basic prompt (weak mock response)
- B: Optimized prompt with few-shot (better mock response)
- C: Structured output (schema-constrained mock)
- D: Retrieval-augmented (mock context improves explanation)
- E: Alternative model (different mock response pattern)
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from config import CATEGORIES, SEVERITIES


def _mock_predict(
    incident: str,
    category_hint: str = "",
    severity_hint: str = "",
    schema_guaranteed: bool = False,
    include_grounded_explanation: bool = False,
    rng: random.Random | None = None,
) -> Dict[str, Any]:
    """Generate a mock model prediction."""
    rng = rng or random.Random(hash(incident) % 2**32)

    # If no hint, pick randomly (simulating a weak model)
    category = category_hint or rng.choice(CATEGORIES)
    severity = severity_hint or rng.choice(SEVERITIES)

    # Simulate occasional errors for weaker baselines
    if rng.random() < 0.15 and not category_hint:
        category = rng.choice([c for c in CATEGORIES if c != category])

    explanation = f"Based on the incident description, this appears to be a {category} issue."
    if include_grounded_explanation:
        explanation = (
            f"Based on retrieved runbook context, the symptoms indicate a "
            f"{category} incident with {severity} severity. The described "
            f"indicators match known {category} failure patterns."
        )

    result = {
        "category": category,
        "severity": severity,
        "explanation": explanation,
    }

    # Baselines without schema guarantee may produce invalid output
    if not schema_guaranteed and rng.random() < 0.05:
        # Simulate missing key
        result.pop("explanation", None)

    return result


# --- Keyword-based classification (simulates what a model would learn) ---

KEYWORDS = {
    "infra": ["disk", "memory", "cpu", "host", "partition", "responsive", "heartbeat"],
    "network": ["latency", "connection", "timeout", "dns", "network", "port", "partition"],
    "db": ["database", "query", "connection pool", "slow", "db"],
    "app": ["application", "error", "500", "response", "memory usage", "latency"],
    "security": ["unauthorized", "ssl", "certificate", "login", "auth", "brute"],
}

SEVERITY_KEYWORDS = {
    "critical": ["unresponsive", "down", "unreachable", "complete", "outage", "compromised"],
    "high": ["spiked", "exceeded", "exhausted", "critical", "high", "immediate"],
    "medium": ["sustained", "degraded", "slow", "trending", "above"],
    "low": ["minor", "within", "no action", "slightly", "no user impact"],
}


def classify_by_keywords(text: str) -> tuple[str, str]:
    """Classify incident by keyword matching — simulates model understanding."""
    text_lower = text.lower()

    # Category
    best_cat = "app"
    best_cat_score = 0
    for cat, kws in KEYWORDS.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > best_cat_score:
            best_cat_score = score
            best_cat = cat

    # Severity
    best_sev = "medium"
    best_sev_score = 0
    for sev, kws in SEVERITY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in text_lower)
        if score > best_sev_score:
            best_sev_score = score
            best_sev = sev

    return best_cat, best_sev


def baseline_a(incident: str, rng: random.Random) -> Dict[str, Any]:
    """Baseline A: Frozen base model, basic prompt — weakest baseline."""
    # Simulate a model that barely understands the task
    cat, sev = classify_by_keywords(incident)
    # Add noise — basic prompt misses some signals
    if rng.random() < 0.25:
        cat = rng.choice(CATEGORIES)
    if rng.random() < 0.30:
        sev = rng.choice(SEVERITIES)
    return _mock_predict(incident, category_hint=cat, severity_hint=sev, rng=rng)


def baseline_b(incident: str, rng: random.Random) -> Dict[str, Any]:
    """Baseline B: Frozen model, optimized prompt with few-shot examples."""
    cat, sev = classify_by_keywords(incident)
    # Optimized prompt reduces errors
    if rng.random() < 0.10:
        cat = rng.choice(CATEGORIES)
    if rng.random() < 0.15:
        sev = rng.choice(SEVERITIES)
    return _mock_predict(incident, category_hint=cat, severity_hint=sev, rng=rng)


def baseline_c(incident: str, rng: random.Random) -> Dict[str, Any]:
    """Baseline C: Frozen model, structured output — schema guaranteed."""
    cat, sev = classify_by_keywords(incident)
    if rng.random() < 0.10:
        cat = rng.choice(CATEGORIES)
    if rng.random() < 0.15:
        sev = rng.choice(SEVERITIES)
    return _mock_predict(
        incident, category_hint=cat, severity_hint=sev,
        schema_guaranteed=True, rng=rng,
    )


def baseline_d(incident: str, rng: random.Random) -> Dict[str, Any]:
    """Baseline D: Frozen model + retrieval — grounded explanation."""
    cat, sev = classify_by_keywords(incident)
    if rng.random() < 0.10:
        cat = rng.choice(CATEGORIES)
    if rng.random() < 0.15:
        sev = rng.choice(SEVERITIES)
    return _mock_predict(
        incident, category_hint=cat, severity_hint=sev,
        schema_guaranteed=True, include_grounded_explanation=True, rng=rng,
    )


def baseline_e(incident: str, rng: random.Random) -> Dict[str, Any]:
    """Baseline E: Alternative model — different error profile."""
    cat, sev = classify_by_keywords(incident)
    # Alternative model has different strengths
    if rng.random() < 0.08:
        cat = rng.choice(CATEGORIES)
    if rng.random() < 0.10:
        sev = rng.choice(SEVERITIES)
    return _mock_predict(
        incident, category_hint=cat, severity_hint=sev,
        schema_guaranteed=True, rng=rng,
    )


BASELINE_FUNCS = {
    "A": baseline_a,
    "B": baseline_b,
    "C": baseline_c,
    "D": baseline_d,
    "E": baseline_e,
}


def run_baseline(baseline_id: str, incidents: List[Dict[str, Any]], seed: int = 42) -> List[Dict[str, Any]]:
    """Run a specific baseline on a list of incidents."""
    rng = random.Random(seed)
    func = BASELINE_FUNCS[baseline_id]
    predictions = []
    for incident in incidents:
        pred = func(incident["input"], rng)
        pred["baseline"] = baseline_id
        pred["input_id"] = hash(incident["input"]) % 2**16
        predictions.append(pred)
    return predictions