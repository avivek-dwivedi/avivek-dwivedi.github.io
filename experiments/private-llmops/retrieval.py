"""
retrieval.py — Mock retrieval and reranking for RAG flows.

Simulates: query transformation, embedding, dense search, reranking.
All operations are synthetic — no real vector database or embedding model.
"""

from __future__ import annotations

import time
import random
from typing import Any, Dict, List


def transform_query(query: str) -> str:
    """Mock query transformation (e.g., HyDE, query expansion)."""
    time.sleep(random.uniform(0.01, 0.05))
    return query.strip().lower()


def embed_query(query: str) -> List[float]:
    """Mock embedding generation — returns a synthetic vector."""
    time.sleep(random.uniform(0.02, 0.08))
    # Return a deterministic pseudo-embedding based on query length
    return [float(ord(c)) / 256.0 for c in query[:128].ljust(128, "\0")]


def dense_search(embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
    """Mock dense vector search — returns synthetic results."""
    time.sleep(random.uniform(0.05, 0.15))
    return [
        {
            "doc_id": f"DOC-{i}",
            "score": random.uniform(0.5, 0.95),
            "content": "Synthetic retrieved content...",
        }
        for i in range(top_k)
    ]


def rerank(query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Mock reranking — reorders results by a synthetic relevance score."""
    time.sleep(random.uniform(0.03, 0.10))
    # Sort by score descending and take top_k
    ranked = sorted(results, key=lambda r: r["score"], reverse=True)
    return ranked[:top_k]


def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Full retrieval pipeline: query transform → embed → dense search → rerank.

    This is the operation that should be wrapped in a retrieval_span.
    Document content is synthetic — no real sensitive data.
    """
    transformed = transform_query(query)
    embedding = embed_query(transformed)
    raw_results = dense_search(embedding, top_k=top_k * 2)
    reranked = rerank(query, raw_results, top_k=top_k)
    return reranked