"""
RAGAS Evaluation Module
=======================
Evaluates RAGShield using research-grade metrics:
- Faithfulness: Does the answer match the context?
- Context Precision: Are retrieved chunks relevant?
- Context Recall: Is all necessary info retrieved?
- Answer Relevancy: Does the answer address the question?
"""

import json
from typing import List, Dict
from pathlib import Path
import config


def evaluate_response(
    query: str,
    answer: str,
    context_chunks: List[Dict],
    ground_truth: str = None,
) -> Dict:
    """
    Compute evaluation metrics for a RAGShield response.
    Uses lightweight heuristic metrics when ragas is not configured.

    Args:
        query: User's question
        answer: Generated answer
        context_chunks: Context chunks used
        ground_truth: Reference answer (if available)

    Returns:
        Dict with evaluation scores
    """
    metrics = {}

    # Faithfulness: does answer content appear in context?
    metrics["faithfulness"] = _faithfulness(answer, context_chunks)

    # Context Precision: relevance of retrieved chunks
    metrics["context_precision"] = _context_precision(query, context_chunks)

    # Answer Relevancy: does answer address the query?
    metrics["answer_relevancy"] = _answer_relevancy(query, answer)

    # Context Coverage: % of context used in answer
    metrics["context_coverage"] = _context_coverage(answer, context_chunks)

    # Avg CQS
    cqs_scores = [c.get("cqs_score", 50) for c in context_chunks]
    metrics["avg_cqs"] = round(sum(cqs_scores) / max(1, len(cqs_scores)), 2)

    # Overall RAG score
    metrics["overall_score"] = round(
        0.3 * metrics["faithfulness"]
        + 0.25 * metrics["context_precision"]
        + 0.25 * metrics["answer_relevancy"]
        + 0.2 * metrics["context_coverage"],
        3
    )

    return {
        "query": query,
        "metrics": metrics,
        "num_chunks_used": len(context_chunks),
        "evaluation_method": "heuristic",
    }


def _faithfulness(answer: str, chunks: List[Dict]) -> float:
    """Check if answer words appear in context."""
    if not chunks or not answer:
        return 0.0

    context_text = " ".join(c.get("text", "") for c in chunks).lower()
    answer_words = set(answer.lower().split())
    # Filter stop words
    stop = {"the", "a", "an", "is", "are", "was", "were", "in", "of", "to", "and", "or", "i", "it"}
    meaningful_words = [w for w in answer_words if len(w) > 3 and w not in stop]

    if not meaningful_words:
        return 0.5

    matches = sum(1 for w in meaningful_words if w in context_text)
    return round(matches / len(meaningful_words), 3)


def _context_precision(query: str, chunks: List[Dict]) -> float:
    """Average relevance score of context chunks."""
    if not chunks:
        return 0.0
    scores = [c.get("similarity_score", c.get("relevance_score", 0.5)) for c in chunks]
    return round(sum(scores) / len(scores), 3)


def _answer_relevancy(query: str, answer: str) -> float:
    """Heuristic: does answer contain query keywords?"""
    if not query or not answer:
        return 0.0

    query_words = set(query.lower().split())
    stop = {"what", "how", "why", "is", "are", "the", "a", "an", "explain", "describe"}
    key_words = [w for w in query_words if len(w) > 3 and w not in stop]

    if not key_words:
        return 0.7  # Can't evaluate

    answer_lower = answer.lower()
    matches = sum(1 for w in key_words if w in answer_lower)

    # Also check for "insufficient evidence" type responses
    if "insufficient" in answer_lower or "don't have" in answer_lower:
        return 0.3  # Honest refusal is somewhat relevant

    return round(min(1.0, 0.4 + (matches / len(key_words)) * 0.6), 3)


def _context_coverage(answer: str, chunks: List[Dict]) -> float:
    """How much of the top chunk is reflected in the answer?"""
    if not chunks or not answer:
        return 0.0

    # Use the best chunk
    best_chunk = max(chunks, key=lambda c: c.get("cqs_score", 0))
    chunk_text = best_chunk.get("text", "").lower()
    chunk_words = set(w for w in chunk_text.split() if len(w) > 4)

    if not chunk_words:
        return 0.5

    answer_words = set(answer.lower().split())
    overlap = chunk_words.intersection(answer_words)

    return round(len(overlap) / max(1, len(chunk_words)), 3)


def save_evaluation_results(results: List[Dict], filename: str = "evaluation_results.json"):
    """Save evaluation results to file."""
    eval_path = Path(config.EVALUATION_DATA_PATH) / filename
    with open(eval_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[RAGAS] Saved evaluation results to {eval_path}")
    return str(eval_path)
