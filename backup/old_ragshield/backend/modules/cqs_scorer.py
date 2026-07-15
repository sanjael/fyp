"""
Context Quality Scorer (CQS) Module
====================================
Computes a composite quality score for each chunk that passed the Context Shield.

Formula:
    CQS = 0.4 × Relevance + 0.3 × Credibility + 0.2 × Consistency + 0.1 × Freshness

Score Interpretation:
    90–100  → Excellent — highly reliable context
    75–89   → Good — trustworthy, minor concerns
    60–74   → Moderate — use with caution
    Below 60 → Poor — risk of unreliable generation
"""

from typing import List, Dict, Optional
import math

import config


class CQSScorer:
    """
    Computes Context Quality Scores for retrieved chunks.
    This score drives the Hallucination Risk Prediction Engine.
    """

    def score_chunks(
        self,
        chunks: List[Dict],
        query: str = "",
        contradiction_pairs: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        Score all passed chunks with CQS and component scores.

        Args:
            chunks: Chunks that passed the Context Shield
            query: Original query (for consistency scoring context)
            contradiction_pairs: Detected contradictions for consistency penalty

        Returns:
            Chunks enriched with CQS score and components
        """
        if not chunks:
            return []

        contradiction_chunk_ids = set()
        if contradiction_pairs:
            for pair in contradiction_pairs:
                contradiction_chunk_ids.update(pair.get("chunk_ids", []))

        scored_chunks = []
        for chunk in chunks:
            scores = self._compute_component_scores(chunk, contradiction_chunk_ids)
            cqs = self._compute_cqs(scores)
            quality_level = self._get_quality_level(cqs)

            scored_chunk = {
                **chunk,
                "cqs_score": round(cqs, 2),
                "quality_level": quality_level,
                "component_scores": scores,
            }
            scored_chunks.append(scored_chunk)

        # Sort by CQS descending
        scored_chunks.sort(key=lambda x: x["cqs_score"], reverse=True)
        return scored_chunks

    def _compute_component_scores(
        self, chunk: Dict, contradiction_ids: set
    ) -> Dict[str, float]:
        """Compute the four component scores for a chunk."""

        # 1. Relevance Score (0–100)
        # From shield's relevance validation (cosine similarity scaled to 0–100)
        relevance_raw = chunk.get("relevance_score", chunk.get("similarity_score", 0.5))
        relevance = min(100.0, relevance_raw * 100.0)

        # 2. Credibility Score (0–100)
        # From source reliability scoring
        credibility = float(chunk.get("source_reliability_score", 50))

        # 3. Consistency Score (0–100)
        # Penalize contradicted chunks
        chunk_id = chunk.get("chunk_id", "")
        if chunk_id in contradiction_ids:
            consistency = 30.0  # Heavy penalty for contradicted content
        elif chunk.get("is_contradicted", False):
            consistency = 40.0
        else:
            consistency = 90.0  # Default: assume consistent

        # Additional penalty if text shows uncertainty markers
        uncertainty_words = ["may", "might", "could", "possibly", "approximately", "roughly"]
        text_lower = chunk.get("text", "").lower()
        uncertainty_count = sum(1 for w in uncertainty_words if f" {w} " in f" {text_lower} ")
        consistency -= min(20.0, uncertainty_count * 5.0)
        consistency = max(0.0, consistency)

        # 4. Freshness Score (0–100)
        # From freshness scoring in Context Shield
        freshness = float(chunk.get("freshness_score", 50))

        return {
            "relevance": round(relevance, 2),
            "credibility": round(credibility, 2),
            "consistency": round(consistency, 2),
            "freshness": round(freshness, 2),
        }

    def _compute_cqs(self, scores: Dict[str, float]) -> float:
        """
        Compute weighted Context Quality Score.
        CQS = 0.4×R + 0.3×C_red + 0.2×C_sis + 0.1×F
        """
        cqs = (
            config.CQS_WEIGHT_RELEVANCE * scores["relevance"]
            + config.CQS_WEIGHT_CREDIBILITY * scores["credibility"]
            + config.CQS_WEIGHT_CONSISTENCY * scores["consistency"]
            + config.CQS_WEIGHT_FRESHNESS * scores["freshness"]
        )
        return min(100.0, max(0.0, cqs))

    def _get_quality_level(self, cqs: float) -> str:
        """Map CQS score to a human-readable quality level."""
        if cqs >= 90:
            return "excellent"
        elif cqs >= 75:
            return "good"
        elif cqs >= 60:
            return "moderate"
        else:
            return "poor"

    def compute_aggregate_cqs(self, scored_chunks: List[Dict]) -> Dict:
        """
        Compute aggregate CQS statistics across all passed chunks.
        Used by the Risk Engine.
        """
        if not scored_chunks:
            return {
                "avg_cqs": 0.0,
                "min_cqs": 0.0,
                "max_cqs": 0.0,
                "std_cqs": 0.0,
                "quality_distribution": {"excellent": 0, "good": 0, "moderate": 0, "poor": 0},
                "overall_quality_level": "poor",
            }

        cqs_values = [c["cqs_score"] for c in scored_chunks]
        avg_cqs = sum(cqs_values) / len(cqs_values)
        min_cqs = min(cqs_values)
        max_cqs = max(cqs_values)

        # Standard deviation
        variance = sum((v - avg_cqs) ** 2 for v in cqs_values) / len(cqs_values)
        std_cqs = math.sqrt(variance)

        quality_distribution = {"excellent": 0, "good": 0, "moderate": 0, "poor": 0}
        for c in scored_chunks:
            level = c.get("quality_level", "poor")
            quality_distribution[level] = quality_distribution.get(level, 0) + 1

        return {
            "avg_cqs": round(avg_cqs, 2),
            "min_cqs": round(min_cqs, 2),
            "max_cqs": round(max_cqs, 2),
            "std_cqs": round(std_cqs, 2),
            "quality_distribution": quality_distribution,
            "overall_quality_level": self._get_quality_level(avg_cqs),
        }
