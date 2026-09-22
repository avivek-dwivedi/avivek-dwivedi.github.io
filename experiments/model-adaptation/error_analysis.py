"""
error_analysis.py — Error categorization and failure analysis.

Analyzes the error distribution across baselines to determine
which intervention is justified.
"""

from __future__ import annotations

from typing import Any, Dict, List

from evaluation import EvalResult
from config import ERROR_CATEGORIES


def analyze_errors(results: List[EvalResult]) -> Dict[str, Any]:
    """
    Analyze the error distribution from a baseline evaluation.

    Returns:
        Analysis with dominant error category, recommendation, and breakdown.
    """
    n = len(results)
    if n == 0:
        return {"error": "no results"}

    error_counts: Dict[str, int] = {}
    for r in results:
        error_counts[r.error_category] = error_counts.get(r.error_category, 0) + 1

    # Sort by frequency
    sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
    dominant_error = sorted_errors[0][0] if sorted_errors[0][0] != "none" else "none"

    # Map dominant error to intervention recommendation
    recommendations = {
        "none": "No fine-tuning needed — baseline already performs well",
        "wrong_category": "Consider SFT for classification accuracy, or better prompting with category definitions",
        "wrong_severity": "Consider SFT for severity calibration, or few-shot examples with severity definitions",
        "schema_invalid": "Use structured decoding — do not fine-tune for formatting",
        "unsupported_statement": "Add retrieval — the model lacks grounding context",
        "missing_explanation": "Structured output constraint or SFT for explanation generation",
    }

    return {
        "total": n,
        "dominant_error": dominant_error,
        "recommendation": recommendations.get(dominant_error, "Investigate further"),
        "error_breakdown": dict(sorted_errors),
        "error_percentages": {k: round(v / n, 4) for k, v in sorted_errors},
    }


def adaptation_decision(
    baseline_results: Dict[str, List[EvalResult]],
    accuracy_threshold: float = 0.90,
) -> Dict[str, Any]:
    """
    Make the adaptation decision based on all baseline results.

    Args:
        baseline_results: Results from all baselines.
        accuracy_threshold: If any baseline exceeds this, do not fine-tune.

    Returns:
        Decision with justification.
    """
    from evaluation import compute_metrics

    best_baseline = None
    best_accuracy = 0.0
    best_results = None

    for baseline_id, results in baseline_results.items():
        metrics = compute_metrics(results)
        full_rate = metrics.get("fully_correct_rate", 0)
        if full_rate > best_accuracy:
            best_accuracy = full_rate
            best_baseline = baseline_id
            best_results = results

    # Decision logic
    if best_accuracy >= accuracy_threshold:
        decision = "do_not_finetune"
        justification = (
            f"Baseline {best_baseline} achieves {best_accuracy:.1%} fully correct rate, "
            f"exceeding the {accuracy_threshold:.0%} threshold. Fine-tuning is not justified."
        )
    elif best_results:
        analysis = analyze_errors(best_results)
        dominant = analysis["dominant_error"]

        if dominant in ("schema_invalid",):
            decision = "structured_decoding"
            justification = f"Dominant error is '{dominant}' — use structured decoding, not fine-tuning."
        elif dominant in ("unsupported_statement",):
            decision = "retrieval"
            justification = f"Dominant error is '{dominant}' — add retrieval for grounding, not fine-tuning."
        elif dominant in ("wrong_category", "wrong_severity", "missing_explanation"):
            decision = "sft_justified"
            justification = (
                f"Best baseline {best_baseline} achieves {best_accuracy:.1%}. "
                f"Dominant error is '{dominant}' — SFT may improve this. "
                f"Proceed to SFT experiment with the established evaluation protocol."
            )
        else:
            decision = "investigate"
            justification = f"Dominant error is '{dominant}' — investigate further before deciding."
    else:
        decision = "no_data"
        justification = "No baseline results available."

    return {
        "decision": decision,
        "best_baseline": best_baseline,
        "best_accuracy": round(best_accuracy, 4),
        "justification": justification,
    }