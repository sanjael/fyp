from typing import List

from langchain_core.documents import Document

from ..config import config
from ..core.base_extractor import BaseFeatureExtractor
from ..models import FeatureResult


# Base credibility by document_type (matches DB enum)
_DOC_TYPE_BASE: dict[str, float] = {
    "academic_paper":           0.95,
    "official_report":          0.85,
    "technical_documentation":  0.80,
    "news_article":             0.60,
    "blog_post":                0.40,
    "social_media":             0.20,
    "unknown":                  0.50,
}

# Trusted domain suffixes — bonus applied when source_url is present
_TRUSTED_DOMAINS = (".gov", ".edu", ".ac.uk", ".ac.", "arxiv.org",
                    "pubmed.ncbi", "ieee.org", "acm.org", "springer.com",
                    "nature.com", "sciencedirect.com")


class SourceCredibilityExtractor(BaseFeatureExtractor):
    """
    Actively infers source credibility from document metadata.

    Scoring cascade (per chunk):
      1. Pre-computed estimated_credibility  → use directly if valid
      2. document_type base score
      3. +0.05 if DOI present
      4. +0.03 if author / document_author present
      5. +0.04 if source_url matches a trusted domain
      6. -0.05 if document_date is absent (unverifiable provenance)
      7. -0.10 if document_type is 'unknown' AND no other signals

    Never silently returns 0.5 without an explanation.
    """

    @property
    def feature_name(self) -> str:
        return "source_credibility"

    def validate(self, query: str, docs: List[Document]) -> bool:
        return bool(docs)

    # ------------------------------------------------------------------
    def _score_single(self, doc: Document) -> tuple[float, str, str]:
        """Return (score, reason, evidence_source) for one chunk."""
        meta = doc.metadata
        signals: list[str] = []

        # 1. Pre-computed value
        precomputed = meta.get("estimated_credibility")
        if precomputed is not None:
            try:
                val = float(precomputed)
                if 0.0 <= val <= 1.0:
                    return val, "Pre-computed estimated_credibility used", "Document Metadata"
            except (ValueError, TypeError):
                pass

        # 2. Document type base
        doc_type = str(meta.get("document_type", "unknown")).lower()
        score = _DOC_TYPE_BASE.get(doc_type, _DOC_TYPE_BASE["unknown"])
        signals.append(f"type={doc_type}({score:.2f})")

        # 3. DOI bonus
        if meta.get("doi"):
            score = min(1.0, score + 0.05)
            signals.append("DOI+0.05")

        # 4. Author bonus
        if meta.get("author") or meta.get("document_author"):
            score = min(1.0, score + 0.03)
            signals.append("author+0.03")

        # 5. Trusted domain bonus
        url = str(meta.get("source_url", "") or "")
        if url and any(d in url for d in _TRUSTED_DOMAINS):
            score = min(1.0, score + 0.04)
            signals.append("trusted_domain+0.04")

        # 6. Missing date penalty
        if not meta.get("document_date"):
            score = max(0.0, score - 0.05)
            signals.append("no_date-0.05")

        # 7. Unknown type with no other signals
        if doc_type == "unknown" and len(signals) == 1:
            score = max(0.0, score - 0.10)
            signals.append("unknown_type_no_signals-0.10")

        reason = "; ".join(signals)
        return round(score, 4), reason, "Document Metadata (inferred)"

    # ------------------------------------------------------------------
    def extract(self, query: str, docs: List[Document]) -> FeatureResult:
        if not docs:
            return FeatureResult(
                score=None,
                confidence=0.0,
                reason="No documents retrieved",
                evidence_source="Unavailable",
            )

        results = [self._score_single(doc) for doc in docs]
        scores = [r[0] for r in results]
        avg_score = sum(scores) / len(scores)

        # Confidence: higher when doc_type is explicit (not 'unknown')
        typed_count = sum(
            1 for doc in docs
            if str(doc.metadata.get("document_type", "unknown")).lower() != "unknown"
        )
        confidence = typed_count / len(docs)

        # Aggregate reasons (deduplicated)
        all_reasons = "; ".join(dict.fromkeys(r[1] for r in results))

        return FeatureResult(
            score=round(max(0.0, min(1.0, avg_score)), 4),
            confidence=round(confidence, 4),
            reason=all_reasons,
            evidence_source="Document Metadata (inferred)",
        )
