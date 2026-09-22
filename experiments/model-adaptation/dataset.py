"""
dataset.py — Synthetic incident dataset generation.

Generates a controlled synthetic dataset of incident descriptions
with ground-truth classification labels. No real customer data.

The dataset is split into train/validation/test with related
document families kept together to prevent leakage.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List

from config import CATEGORIES, SEVERITIES

# --- Incident templates per category ---
# Each template is a family — paraphrases of the same incident type.
# All paraphrases in a family go to the same split to prevent leakage.

INCIDENT_FAMILIES: Dict[str, List[Dict[str, Any]]] = {
    "infra": [
        {
            "category": "infra",
            "severity": "high",
            "templates": [
                "Disk usage on {host} reached {pct}% on the root partition. "
                "System may become unresponsive if not addressed.",
                "Root filesystem on {host} is at {pct}% capacity. "
                "Immediate action required to prevent disk full condition.",
                "Storage alert: {host} root partition {pct}% full. "
                "Risk of system instability if disk exhausts.",
            ],
        },
        {
            "category": "infra",
            "severity": "medium",
            "templates": [
                "CPU utilization on {host} sustained at {pct}% for 10 minutes. "
                "No user impact reported yet.",
                "High CPU on {host} — {pct}% average over last 10 min. "
                "Monitoring for further degradation.",
                "{host} CPU usage at {pct}%. Sustained load detected "
                "but services remain responsive.",
            ],
        },
        {
            "category": "infra",
            "severity": "critical",
            "templates": [
                "Host {host} is unresponsive. Heartbeat lost at {time}. "
                "All services on this host are down.",
                "No response from {host} since {time}. "
                "Host appears frozen — full outage.",
                "{host} stopped responding at {time}. "
                "Complete infrastructure failure on this node.",
            ],
        },
    ],
    "network": [
        {
            "category": "network",
            "severity": "high",
            "templates": [
                "Network latency between {host} and {service} spiked to {ms}ms. "
                "Normal baseline is under 5ms.",
                "High latency detected: {host} → {service} at {ms}ms RTT. "
                "Significantly above baseline.",
                "Inter-service latency {host} to {service}: {ms}ms. "
                "Potential network path degradation.",
            ],
        },
        {
            "category": "network",
            "severity": "low",
            "templates": [
                "DNS resolution for {service} took {ms}ms. "
                "Within acceptable range but above average.",
                "Minor latency on {host} connection to {service}. "
                "{ms}ms — no user impact.",
                "Slightly elevated network delay to {service} ({ms}ms). "
                "No action needed.",
            ],
        },
        {
            "category": "network",
            "severity": "critical",
            "templates": [
                "Connection timeout from {host} to {service} on port {port}. "
                "Service is unreachable.",
                "Cannot reach {service}:{port} from {host}. "
                "Complete network partition detected.",
                "Network partition: {host} cannot connect to {service} "
                "on port {port}. All requests timing out.",
            ],
        },
    ],
    "db": [
        {
            "category": "db",
            "severity": "high",
            "templates": [
                "Database {service} connection pool exhausted. "
                "{count} connections in use, max {max_conn}.",
                "Connection pool for {service} is full. "
                "{count}/{max_conn} connections active. New requests queued.",
                "{service} database: {count} of {max_conn} pool connections "
                "in use. Pool exhaustion imminent.",
            ],
        },
        {
            "category": "db",
            "severity": "critical",
            "templates": [
                "Database {service} is down. All queries returning errors. "
                "Data availability compromised.",
                "{service} database unreachable. "
                "All read and write operations failing.",
                "Complete database outage on {service}. "
                "No queries can be served.",
            ],
        },
        {
            "category": "db",
            "severity": "medium",
            "templates": [
                "Slow query detected on {service}. Query took {ms}ms, "
                "threshold is 1000ms.",
                "{service} database: query exceeded slow-query threshold "
                "at {ms}ms.",
                "Long-running query on {service} ({ms}ms). "
                "May indicate missing index or lock contention.",
            ],
        },
    ],
    "app": [
        {
            "category": "app",
            "severity": "high",
            "templates": [
                "Application {service} returning 500 errors. "
                "Error rate at {pct}% of requests.",
                "{service} error rate: {pct}% HTTP 500. "
                "Application crash suspected.",
                "High error rate on {service}: {pct}% of requests failing "
                "with server errors.",
            ],
        },
        {
            "category": "app",
            "severity": "low",
            "templates": [
                "Application {service} memory usage at {pct}%. "
                "Within limits but trending upward.",
                "{service} app instance using {pct}% of allocated memory. "
                "Monitor for leak.",
                "Memory utilization on {service}: {pct}%. "
                "No action required yet.",
            ],
        },
        {
            "category": "app",
            "severity": "medium",
            "templates": [
                "{service} response time degraded to {ms}ms. "
                "SLA threshold is 500ms.",
                "Application {service} latency: {ms}ms p95. "
                "Exceeding SLA target.",
                "{service} p95 latency at {ms}ms — above the 500ms SLA. "
                "User experience impacted.",
            ],
        },
    ],
    "security": [
        {
            "category": "security",
            "severity": "critical",
            "templates": [
                "Unauthorized access attempt from IP {ip} to {service}. "
                "Multiple failed authentication attempts detected.",
                "Security alert: brute force attack on {service} from {ip}. "
                "Immediate investigation required.",
                "Repeated auth failures from {ip} targeting {service}. "
                "Potential intrusion attempt.",
            ],
        },
        {
            "category": "security",
            "severity": "high",
            "templates": [
                "SSL certificate for {service} expires in {count} days. "
                "Renewal required to prevent service disruption.",
                "{service} TLS certificate expiring in {count} days. "
                "Action needed to avoid certificate errors.",
                "Certificate warning: {service} cert expires in {count} days. "
                "Schedule renewal.",
            ],
        },
        {
            "category": "security",
            "severity": "medium",
            "templates": [
                "Failed login from user {user} on {service}. "
                "Account locked after {count} attempts.",
                "{user} account on {service} locked due to {count} "
                "failed authentication attempts.",
                "Security event: {user} triggered account lockout on "
                "{service} after {count} failures.",
            ],
        },
    ],
}

# Fill values for template placeholders
FILL_VALUES = {
    "host": ["web-01", "web-02", "db-01", "api-03", "worker-05", "cache-01"],
    "service": ["auth-service", "payment-api", "user-db", "redis-cache", "nginx-proxy"],
    "pct": ["85", "90", "92", "78", "95"],
    "ms": ["250", "500", "1200", "3000", "800"],
    "time": ["14:32 UTC", "09:15 UTC", "23:47 UTC", "06:03 UTC"],
    "port": ["443", "5432", "8080", "6379"],
    "count": ["5", "10", "15", "20", "3"],
    "max_conn": ["100", "50", "200"],
    "ip": ["192.168.1.100", "10.0.0.50", "172.16.0.25"],
    "user": ["admin", "svc_account", "deploy_user"],
}


def fill_template(template: str, rng: random.Random) -> str:
    """Fill template placeholders with random values."""
    result = template
    for key, values in FILL_VALUES.items():
        placeholder = "{" + key + "}"
        while placeholder in result:
            result = result.replace(placeholder, rng.choice(values), 1)
    return result


def generate_dataset(
    num_per_family: int = 5,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic incident dataset.

    Each family produces num_per_family examples by sampling templates
    and filling placeholders. All examples from the same family go to
    the same split to prevent leakage.

    Returns:
        List of examples with keys: input, category, severity, explanation, family_id
    """
    rng = random.Random(seed)
    examples = []
    family_id = 0

    for category in INCIDENT_FAMILIES:
        for family in INCIDENT_FAMILIES[category]:
            for _ in range(num_per_family):
                template = rng.choice(family["templates"])
                filled = fill_template(template, rng)

                # Generate a grounded explanation
                explanation = (
                    f"Incident classified as {family['category']} with "
                    f"{family['severity']} severity based on the described symptoms."
                )

                examples.append({
                    "input": filled,
                    "category": family["category"],
                    "severity": family["severity"],
                    "explanation": explanation,
                    "family_id": family_id,
                })
            family_id += 1

    return examples


def split_dataset(
    examples: List[Dict[str, Any]],
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    seed: int = 42,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Split dataset into train/validation/test.

    Related document families (same family_id) are kept together
    to prevent train-test leakage.
    """
    rng = random.Random(seed)

    # Group by family
    families: Dict[int, List[Dict[str, Any]]] = {}
    for ex in examples:
        families.setdefault(ex["family_id"], []).append(ex)

    family_ids = list(families.keys())
    rng.shuffle(family_ids)

    n = len(family_ids)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)

    train_families = family_ids[:n_train]
    val_families = family_ids[n_train : n_train + n_val]
    test_families = family_ids[n_train + n_val :]

    splits = {"train": [], "validation": [], "test": []}
    for fid in train_families:
        splits["train"].extend(families[fid])
    for fid in val_families:
        splits["validation"].extend(families[fid])
    for fid in test_families:
        splits["test"].extend(families[fid])

    return splits


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic incident dataset")
    parser.add_argument("--output", default="data/incidents.jsonl", help="Output file path")
    parser.add_argument("--num-per-family", type=int, default=5, help="Examples per family")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    examples = generate_dataset(num_per_family=args.num_per_family, seed=args.seed)
    splits = split_dataset(examples, seed=args.seed)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for ex in splits["train"]:
            ex_copy = {**ex, "split": "train"}
            f.write(json.dumps(ex_copy) + "\n")
        for ex in splits["validation"]:
            ex_copy = {**ex, "split": "validation"}
            f.write(json.dumps(ex_copy) + "\n")
        for ex in splits["test"]:
            ex_copy = {**ex, "split": "test"}
            f.write(json.dumps(ex_copy) + "\n")

    print(f"Generated {len(examples)} examples:")
    print(f"  Train: {len(splits['train'])}")
    print(f"  Validation: {len(splits['validation'])}")
    print(f"  Test: {len(splits['test'])}")
    print(f"  Families: {len(set(ex['family_id'] for ex in examples))}")
    print(f"  Output: {output_path}")


if __name__ == "__main__":
    main()