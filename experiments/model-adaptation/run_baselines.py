"""
run_baselines.py — Run all baselines on the test set.

Generates the dataset, runs all 5 baselines (A-E) on the test split,
and saves raw predictions to results/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataset import generate_dataset, split_dataset
from baselines import run_baseline, BASELINE_FUNCS
from config import BASELINES


def main():
    parser = argparse.ArgumentParser(description="Run all baselines on the test set")
    parser.add_argument("--num-per-family", type=int, default=5, help="Examples per family")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    args = parser.parse_args()

    # Generate dataset
    print("Generating synthetic dataset...")
    examples = generate_dataset(num_per_family=args.num_per_family, seed=args.seed)
    splits = split_dataset(examples, seed=args.seed)
    test_set = splits["test"]

    print(f"Test set size: {len(test_set)}")

    # Run each baseline
    results_dir = Path(args.output_dir)
    results_dir.mkdir(exist_ok=True)

    all_predictions = {}
    for baseline_id in BASELINE_FUNCS:
        print(f"\nRunning Baseline {baseline_id}: {BASELINES[baseline_id]['name']}")
        predictions = run_baseline(baseline_id, test_set, seed=args.seed)
        all_predictions[baseline_id] = predictions

        # Save predictions
        output_file = results_dir / f"baseline_{baseline_id}_predictions.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(predictions, f, indent=2)
        print(f"  Saved {len(predictions)} predictions to {output_file}")

    # Save ground truth
    gt_file = results_dir / "ground_truth.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2)
    print(f"\nSaved ground truth to {gt_file}")

    print("\n✅ All baselines complete. Run 'python run_evaluation.py' to score.")


if __name__ == "__main__":
    main()