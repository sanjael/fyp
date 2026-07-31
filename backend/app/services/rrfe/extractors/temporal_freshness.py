import math
from datetime import datetime, timezone
from typing import List

from langchain_core.documents import Document

from app.core.date_parser import extract_doc_datetime
from ..config import config
from ..core.base_extractor import BaseFeatureExtractor
from ..models import FeatureResult


class TemporalFreshnessExtractor(BaseFeatureExtractor):
    """
    Computes how recent the retrieved documents are using exponential half-life decay.

    Formula:  score = exp(-(ln2 / half_life) * age_days)
    Half-life = 180 days  →  score = 0.5 at 180 days, 0.25 at 360 days.

    IMPORTANT: ingestion_date is NEVER used as a proxy for document_date.
    If document_date is absent the chunk contributes NULL (confidence = 0).
    """

    _LAMBDA: float = math.log(2) / config.FRESHNESS_HALF_LIFE_DAYS

    @property
    def feature_name(self) -> str:
        return "temporal_freshness"

    def validate(self, query: str, docs: List[Document]) -> bool:
        return bool(docs)

    def extract(self, query: str, docs: List[Document]) -> FeatureResult:
        if not docs:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason="No documents retrieved",
                evidence_source="Unavailable",
            )

        now = datetime.now(timezone.utc)
        scored = 0.0
        dated_count = 0

        for doc in docs:
            doc_date = extract_doc_datetime(doc.metadata, text_content=doc.page_content)
            if doc_date is None:
                continue
            age_days = max(0, (now - doc_date).days)
            scored += math.exp(-self._LAMBDA * age_days)
            dated_count += 1

        if dated_count == 0:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason="No publication date found in metadata across retrieved chunks",
                evidence_source="Unavailable",
            )

        avg_score = scored / dated_count
        # Confidence scales with the fraction of chunks that had a date
        confidence = dated_count / len(docs)

        return FeatureResult(
            score=round(max(0.0, min(1.0, avg_score)), 4),
            confidence=round(confidence, 4),
            reason=(
                f"{dated_count}/{len(docs)} chunks had document_date. "
                f"Exponential decay (half-life={config.FRESHNESS_HALF_LIFE_DAYS}d) applied."
            ),
            evidence_source="Document Metadata (document_date)",
        )
