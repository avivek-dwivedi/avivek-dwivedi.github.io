"""
evaluation.py — Scoring and metrics for the adaptation evaluation lab.

Scores predictions against ground truth using the pre-defined
error taxonomy. Computes aggregate metrics and per-category breakdowns.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from config import TASK, ERROR_CATEGORIES


@dataclass
class EvalResult:
    """Result of scoring a single prediction."""
    category_correct: bool
    severity_correct: bool
    schema_valid: bool
    error_category: str
    baseline: str = ""

    @property
    def fully_correct(self) -> bool:
        """Both category and severity correct, and schema valid."""
        return self.category_correct and self.severity_correct and self.schema_valid


def score_prediction(prediction: Dict[str, Any], ground_truth: Dict[str, Any]) -> EvalResult:
    """Score a single prediction against ground truth."""
    schema_ok = TASK.validate_output(prediction)
    cat_ok = prediction.get("category") == ground_truth["category"]
    sev_ok = prediction.get("severity") == ground_truth["severity"]

    # Determine error category using the pre-defined taxonomy
    if not schema_ok:
        err = "schema_invalid"
    elif not cat_ok:
        err = "wrong_category"
    elif not sev_ok:
        err = "wrong_severity"
    elif not prediction.get("explanation"):
        err = "missing_explanation"
    else:
        err = "none"

    return EvalResult(
        category_correct=cat_ok,
        severity_correct=sev_ok,
        schema_valid=schema_ok,
        error_category=err,
        baseline=prediction.get("baseline", ""),
    )


def score_baseline(
    predictions: List[Dict[str, Any]],
    ground_truths: List[Dict[str, Any]],
) -> List[EvalResult]:
    """Score all predictions for a baseline."""
    results = []
    for pred, gt in zip(predictions, ground_truths):
        results.append(score_prediction(pred, gt))
    return results


def compute_metrics(results: List[EvalResult]) -> Dict[str, Any]:
    """Compute aggregate metrics from a list of EvalResults."""
    n = len(results)
    if n == 0:
        return {"error": "no results"}

    category_accuracy = sum(1 for r in results if r.category_correct) / n
    severity_accuracy = sum(1 for r in results if r.severity_correct) / n
    schema_validity = sum(1 for r in results if r.schema_valid) / n
    fully_correct = sum(1 for r in results if r.fully_correct) / n

    # Error category distribution
    error_dist: Dict[str, int] = {}
    for r in results:
        error_dist[r.error_category] = error_dist.get(r.error_category, 0) + 1

    error_dist_pct = {k: v / n for k, v in error_dist.items()}

    return {
        "n": n,
        "category_accuracy": round(category_accuracy, 4),
        "severity_accuracy": round(severity_accuracy, 4),
        "schema_validity": round(schema_validity, 4),
        "fully_correct_rate": round(fully_correct, 4),
        "error_distribution": error_dist,
        "error_distribution_pct": {k: round(v, 4) for k, v in error_dist_pct.items()},
    }


def compare_baselines(
    all_results: Dict[str, List[EvalResult]],
) -> Dict[str, Any]:
    """Compare metrics across all baselines."""
    comparison = {}
    for baseline_id, results in all_results.items():
        comparison[baseline_id] = compute_metrics(results)
    return comparison


def print_comparison(comparison: Dict[str, Any]) -> None:
    """Print a human-readable comparison table."""
    print(f"\n{'Baseline':<12} {'Cat Acc':>10} {'Sev Acc':>10} {'Schema':>10} {'Full':>10} {'Dominant Error':>20}")
    print(f"{'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*20}")

    for baseline_id, metrics in comparison.items():
        if "error" in metrics:
            print(f"{baseline_id:<12} {'ERROR':>10}")
            continue

        # Find dominant error
        err_dist = metrics.get("error_distribution", {})
        dominant = max(err_dist.items(), key=lambda x: x[1]) if err_dist else ("none", 0)

        print(
            f"{baseline_id:<12} "
            f"{metrics['category_accuracy']:>10.1%} "
            f"{metrics['severity_accuracy']:>10.1%} "
            f"{metrics['schema_validity']:>10.1%} "
            f"{metrics['fully_correct_rate']:>10.1%} "
            f"{dominant[0]:>20}"
        )

    print()
    print("Error category descriptions:")
    for cat, desc in ERROR_CATEGORIES.items():
        print(f"  {cat}: {desc}")