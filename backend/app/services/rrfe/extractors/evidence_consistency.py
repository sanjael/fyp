from typing import List, Protocol

import numpy as np
from langchain_core.documents import Document
from sklearn.metrics.pairwise import cosine_similarity

from ..config import config
from ..core.base_extractor import BaseFeatureExtractor
from ..models import FeatureResult
from ...embedding_provider import embeddings


# ---------------------------------------------------------------------------
# Pluggable contradiction detector interface
# Future NLI / LLM-based detectors implement this protocol without changing
# the EvidenceConsistencyExtractor interface.
# ---------------------------------------------------------------------------

class ContradictionDetector(Protocol):
    """Protocol for pluggable contradiction detection backends."""
    def detect(self, texts: list[str]) -> float:
        """Return a contradiction penalty in [0, 1]. 0 = no contradiction."""
        ...


class VarianceContradictionDetector:
    """
    Lightweight default detector.
    Uses pairwise cosine-similarity variance as a proxy for contradiction:
      - Low variance + high mean  → consistent, on-topic chunks
      - High variance             → some chunk pairs are semantically distant
                                    (potential contradiction or off-topic noise)
    """
    def detect(self, vectors: np.ndarray) -> tuple[float, float, float]:
        """Return (avg_sim, variance, penalty) from pre-computed embedding matrix."""
        sim_matrix = cosine_similarity(vectors)
        idx = np.triu_indices_from(sim_matrix, k=1)
        pairwise = sim_matrix[idx]
        if len(pairwise) == 0:
            return 0.5, 0.0, 0.0
        avg_sim = float(np.mean(pairwise))
        variance = float(np.var(pairwise))
        # Penalty: variance / threshold, capped at 1.0
        penalty = min(1.0, variance / config.CONSISTENCY_VARIANCE_PENALTY_THRESHOLD)
        return avg_sim, variance, penalty


class EvidenceConsistencyExtractor(BaseFeatureExtractor):
    """
    Measures how internally consistent the retrieved evidence set is.

    score = avg_pairwise_cosine_sim * (1 - variance_penalty)

    The ContradictionDetector is injected so future NLI or LLM-based
    detectors can be swapped in without touching this class.
    """

    def __init__(self, detector: VarianceContradictionDetector | None = None):
        self._detector = detector or VarianceContradictionDetector()

    @property
    def feature_name(self) -> str:
        return "evidence_consistency"

    def extract(self, query: str, docs: List[Document]) -> FeatureResult:
        if not docs or len(docs) < 2:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason="Fewer than 2 chunks retrieved; consistency cannot be measured",
                evidence_source="Unavailable",
            )

        try:
            texts = [doc.page_content for doc in docs]
            vectors = np.array(embeddings.embed_documents(texts))

            avg_sim, variance, penalty = self._detector.detect(vectors)
            score = avg_sim * (1.0 - penalty)

            confidence = 1.0 - penalty  # High penalty → low confidence in consistency

            reason = (
                f"avg_cosine_sim={avg_sim:.3f}, "
                f"pairwise_variance={variance:.4f}, "
                f"contradiction_penalty={penalty:.3f}"
            )

            return FeatureResult(
                score=round(max(0.0, min(1.0, score)), 4),
                confidence=round(max(0.0, min(1.0, confidence)), 4),
                reason=reason,
                evidence_source="Embedding Space (pairwise cosine similarity)",
            )

        except Exception as exc:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason=f"Extraction failed: {exc}",
                evidence_source="Unavailable",
            )
