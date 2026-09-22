"""
config.py — Task specification and configuration for the adaptation evaluation lab.

Defines:
- The task (incident classification + grounded explanation)
- Output schema
- Error categories
- Evaluation metrics
- Baseline definitions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# --- Task definition ---

CATEGORIES = ["infra", "network", "db", "app", "security"]
SEVERITIES = ["low", "medium", "high", "critical"]

EXPECTED_OUTPUT_KEYS = ["category", "severity", "explanation"]

# Pre-defined error taxonomy — defined BEFORE evaluation, not post-hoc
ERROR_CATEGORIES = {
    "none": "No error — prediction matches ground truth",
    "wrong_category": "Category classification is incorrect",
    "wrong_severity": "Severity classification is incorrect",
    "schema_invalid": "Output does not match expected schema",
    "unsupported_statement": "Explanation contains unsupported claims",
    "missing_explanation": "Explanation is empty or missing",
}

# --- Baseline definitions ---

BASELINES = {
    "A": {
        "name": "Frozen base model, basic prompt",
        "description": "Straightforward prompt with no examples or context",
        "uses_retrieval": False,
        "uses_few_shot": False,
    },
    "B": {
        "name": "Frozen model, optimized prompt",
        "description": "Carefully constructed prompt with few-shot examples",
        "uses_retrieval": False,
        "uses_few_shot": True,
    },
    "C": {
        "name": "Frozen model, structured output",
        "description": "Schema-constrained output format",
        "uses_retrieval": False,
        "uses_few_shot": True,
    },
    "D": {
        "name": "Frozen model + retrieval",
        "description": "Relevant runbook context provided",
        "uses_retrieval": True,
        "uses_few_shot": True,
    },
    "E": {
        "name": "Alternative model",
        "description": "Different base model with optimized prompt",
        "uses_retrieval": False,
        "uses_few_shot": True,
    },
}


@dataclass
class TaskSpec:
    """Task specification — defines what 'correct' means."""
    name: str = "incident_classification"
    input_description: str = "Sanitized incident description"
    output_keys: List[str] = field(default_factory=lambda: EXPECTED_OUTPUT_KEYS.copy())
    categories: List[str] = field(default_factory=lambda: CATEGORIES.copy())
    severities: List[str] = field(default_factory=lambda: SEVERITIES.copy())

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """Check if an output has the required keys with valid values."""
        if not all(k in output for k in self.output_keys):
            return False
        if output["category"] not in self.categories:
            return False
        if output["severity"] not in self.severities:
            return False
        if not output.get("explanation"):
            return False
        return True


# Default task specification
TASK = TaskSpec()