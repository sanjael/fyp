from typing import List

import numpy as np
from langchain_core.documents import Document
from sklearn.metrics.pairwise import cosine_similarity

from ..config import config
from ..core.base_extractor import BaseFeatureExtractor
from ..models import FeatureResult
from ...embedding_provider import embeddings


class EvidenceSufficiencyExtractor(BaseFeatureExtractor):
    """
    Measures how well the retrieved evidence set covers the query.

    score = MAX_WEIGHT * max_sim + MEAN_WEIGHT * mean_sim

    Rationale:
      max_sim  → at least one chunk must be highly relevant
      mean_sim → the whole retrieved set should be on-topic

    Also returns coverage_percentage: fraction of chunks above a
    relevance threshold (0.5), useful for the explainability card.
    """

    _RELEVANCE_THRESHOLD = 0.5

    @property
    def feature_name(self) -> str:
        return "evidence_sufficiency"

    def extract(self, query: str, docs: List[Document]) -> FeatureResult:
        if not docs or not query:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason="No documents or empty query",
                evidence_source="Unavailable",
            )

        try:
            q_vec = np.array(embeddings.embed_query(query)).reshape(1, -1)
            d_vecs = np.array(embeddings.embed_documents(
                [doc.page_content for doc in docs]
            ))

            sims = cosine_similarity(q_vec, d_vecs)[0]

            max_sim = float(np.max(sims))
            mean_sim = float(np.mean(sims))
            score = (
                config.SUFFICIENCY_MAX_WEIGHT * max_sim
                + config.SUFFICIENCY_MEAN_WEIGHT * mean_sim
            )

            # Coverage: fraction of chunks above relevance threshold
            above_threshold = int(np.sum(sims >= self._RELEVANCE_THRESHOLD))
            coverage_pct = round(above_threshold / len(docs) * 100, 1)

            # Confidence: scales with coverage percentage
            confidence = above_threshold / len(docs)

            reason = (
                f"max_sim={max_sim:.3f}, mean_sim={mean_sim:.3f}, "
                f"coverage={coverage_pct}% chunks ≥ {self._RELEVANCE_THRESHOLD} threshold"
            )

            return FeatureResult(
                score=round(max(0.0, min(1.0, score)), 4),
                confidence=round(max(0.0, min(1.0, confidence)), 4),
                reason=reason,
                evidence_source="Embedding Space (query-document cosine similarity)",
            )

        except Exception as exc:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason=f"Extraction failed: {exc}",
                evidence_source="Unavailable",
            )
