"""
run_evaluation.py — Score predictions and make the adaptation decision.

Loads predictions from all baselines, scores them against ground truth,
computes metrics, analyzes errors, and outputs the adaptation decision.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation import score_baseline, compute_metrics, compare_baselines, print_comparison
from error_analysis import analyze_errors, adaptation_decision
from contamination import run_all_checks


def main():
    parser = argparse.ArgumentParser(description="Score and compare baseline results")
    parser.add_argument("--results-dir", default="results", help="Results directory")
    parser.add_argument("--threshold", type=float, default=0.90, help="Accuracy threshold for fine-tuning decision")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    # Load ground truth
    gt_file = results_dir / "ground_truth.json"
    if not gt_file.exists():
        print(f"❌ Ground truth file not found: {gt_file}")
        print("Run 'python run_baselines.py' first.")
        return

    with open(gt_file, "r", encoding="utf-8") as f:
        ground_truths = json.load(f)

    # Load and score each baseline
    all_results = {}
    baseline_files = sorted(results_dir.glob("baseline_*_predictions.json"))

    if not baseline_files:
        print(f"❌ No baseline prediction files found in {results_dir}")
        print("Run 'python run_baselines.py' first.")
        return

    for pred_file in baseline_files:
        baseline_id = pred_file.stem.split("_")[1]

        with open(pred_file, "r", encoding="utf-8") as f:
            predictions = json.load(f)

        results = score_baseline(predictions, ground_truths)
        all_results[baseline_id] = results
        print(f"Scored Baseline {baseline_id}: {len(results)} predictions")

    # Compare
    comparison = compare_baselines(all_results)
    print_comparison(comparison)

    # Error analysis for each baseline
    print("\n" + "=" * 60)
    print("Error Analysis")
    print("=" * 60)
    for baseline_id, results in all_results.items():
        analysis = analyze_errors(results)
        print(f"\nBaseline {baseline_id}:")
        print(f"  Dominant error: {analysis['dominant_error']}")
        print(f"  Recommendation: {analysis['recommendation']}")
        print(f"  Error breakdown: {analysis['error_breakdown']}")

    # Adaptation decision
    print("\n" + "=" * 60)
    print("Adaptation Decision")
    print("=" * 60)
    decision = adaptation_decision(all_results, accuracy_threshold=args.threshold)
    print(f"\nDecision: {decision['decision']}")
    print(f"Best baseline: {decision['best_baseline']} ({decision['best_accuracy']:.1%})")
    print(f"Justification: {decision['justification']}")

    # Save full report
    report = {
        "comparison": comparison,
        "decision": decision,
        "error_analysis": {
            bid: analyze_errors(results) for bid, results in all_results.items()
        },
    }

    report_file = results_dir / "evaluation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Full report saved to {report_file}")

    # Data integrity check
    print("\n" + "=" * 60)
    print("Data Integrity Check")
    print("=" * 60)
    # Note: This requires the full dataset — in production, load from data/
    print("Run contamination checks on the full dataset before training.")
    print("See contamination.py for dedup, near-duplicate, and leakage detection.")


if __name__ == "__main__":
    main()