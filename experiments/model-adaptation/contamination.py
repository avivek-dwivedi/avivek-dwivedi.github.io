"""
contamination.py — Contamination and deduplication checks.

Checks for:
- Exact duplicates within the dataset
- Near-duplicate detection (simple n-gram overlap)
- Cross-split contamination (train/test leakage)
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def find_exact_duplicates(examples: List[Dict[str, Any]]) -> List[str]:
    """Find exact duplicate inputs in the dataset."""
    inputs = [ex["input"] for ex in examples]
    counts = Counter(inputs)
    return [text for text, count in counts.items() if count > 1]


def ngram_set(text: str, n: int = 5) -> set:
    """Extract n-grams from text."""
    words = text.lower().split()
    if len(words) < n:
        return {text.lower()}
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(a: set, b: set) -> float:
    """Jaccard similarity between two sets."""
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union)


def find_near_duplicates(
    examples: List[Dict[str, Any]],
    threshold: float = 0.7,
    ngram_size: int = 5,
) -> List[tuple]:
    """
    Find near-duplicate pairs using n-gram Jaccard similarity.

    Returns:
        List of (index_a, index_b, similarity) tuples above threshold.
    """
    ngram_sets = [ngram_set(ex["input"], ngram_size) for ex in examples]
    duplicates = []

    for i in range(len(ngram_sets)):
        for j in range(i + 1, len(ngram_sets)):
            sim = jaccard_similarity(ngram_sets[i], ngram_sets[j])
            if sim >= threshold:
                duplicates.append((i, j, sim))

    return duplicates


def check_cross_split_contamination(
    train: List[Dict[str, Any]],
    test: List[Dict[str, Any]],
    ngram_size: int = 5,
    threshold: float = 0.8,
) -> List[tuple]:
    """
    Check for contamination between train and test splits.

    Returns:
        List of (train_index, test_index, similarity) tuples above threshold.
    """
    train_ngrams = [ngram_set(ex["input"], ngram_size) for ex in train]
    test_ngrams = [ngram_set(ex["input"], ngram_size) for ex in test]

    contamination = []
    for i, tn in enumerate(train_ngrams):
        for j, te in enumerate(test_ngrams):
            sim = jaccard_similarity(tn, te)
            if sim >= threshold:
                contamination.append((i, j, sim))

    return contamination


def check_family_leakage(
    train: List[Dict[str, Any]],
    test: List[Dict[str, Any]],
) -> List[int]:
    """
    Check that no family_id appears in both train and test.

    Returns:
        List of family_ids that leaked across splits.
    """
    train_families = {ex["family_id"] for ex in train}
    test_families = {ex["family_id"] for ex in test}
    leaked = list(train_families & test_families)
    return leaked


def run_all_checks(
    train: List[Dict[str, Any]],
    validation: List[Dict[str, Any]],
    test: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Run all data integrity checks."""
    all_examples = train + validation + test

    return {
        "exact_duplicates": find_exact_duplicates(all_examples),
        "near_duplicates": find_near_duplicates(all_examples),
        "train_test_contamination": check_cross_split_contamination(train, test),
        "train_validation_contamination": check_cross_split_contamination(train, validation),
        "family_leakage_train_test": check_family_leakage(train, test),
        "family_leakage_train_val": check_family_leakage(train, validation),
        "total_examples": len(all_examples),
        "train_size": len(train),
        "validation_size": len(validation),
        "test_size": len(test),
    }