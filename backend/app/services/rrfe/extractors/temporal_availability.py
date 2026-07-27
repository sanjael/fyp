from typing import List

from langchain_core.documents import Document

from ..core.base_extractor import BaseFeatureExtractor
from ..models import FeatureResult, TemporalAvailabilityResult


# Score assigned to each availability tier
_AVAILABILITY_SCORES = {
    "Available": 1.0,   # Explicit document_date in metadata
    "Estimated": 0.5,   # Date inferred from ingestion_date or filename heuristic
    "Unknown": 0.0,     # No date signal at all
}


class TemporalAvailabilityExtractor(BaseFeatureExtractor):
    """
    Determines whether the publication date of retrieved documents can be identified.

    This is SEPARATE from Temporal Freshness:
      - Freshness  = how recent the document is (requires a known date)
      - Availability = whether a date can even be determined

    Returns a TemporalAvailabilityResult (subclass of FeatureResult) so the
    availability_status field is accessible for explainability cards.
    """

    @property
    def feature_name(self) -> str:
        return "temporal_availability"

    def validate(self, query: str, docs: List[Document]) -> bool:
        return bool(docs)

    def _classify_doc(self, doc: Document) -> tuple[str, str]:
        """Return (status, reason) for a single document chunk."""
        meta = doc.metadata

        if meta.get("document_date"):
            return "Available", "Explicit document_date found in chunk metadata"

        # Heuristic: ingestion_date exists but no document_date
        if meta.get("ingestion_date"):
            return "Estimated", "Only ingestion_date available; document_date unknown"

        # Heuristic: filename contains a 4-digit year
        filename = str(meta.get("filename", "") or meta.get("document_filename", ""))
        import re
        if re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", filename):
            return "Estimated", f"Year pattern detected in filename: {filename}"

        return "Unknown", "No date signal found in metadata or filename"

    def extract(self, query: str, docs: List[Document]) -> TemporalAvailabilityResult:
        if not docs:
            return TemporalAvailabilityResult(
                score=0.0,
                confidence=0.0,
                reason="No documents retrieved",
                evidence_source="None",
                availability_status="Unknown",
            )

        statuses = [self._classify_doc(doc) for doc in docs]
        status_values = [s[0] for s in statuses]
        reasons = [s[1] for s in statuses]

        # Aggregate: use the best available status across all chunks
        if "Available" in status_values:
            agg_status = "Available"
            available_count = status_values.count("Available")
            agg_reason = (
                f"{available_count}/{len(docs)} chunks have explicit document_date"
            )
            confidence = available_count / len(docs)
        elif "Estimated" in status_values:
            agg_status = "Estimated"
            est_count = status_values.count("Estimated")
            agg_reason = (
                f"{est_count}/{len(docs)} chunks have estimated date only"
            )
            confidence = 0.5
        else:
            agg_status = "Unknown"
            agg_reason = "No date signal found in any retrieved chunk"
            confidence = 0.0

        score = _AVAILABILITY_SCORES[agg_status]

        return TemporalAvailabilityResult(
            score=round(score, 4),
            confidence=round(confidence, 4),
            reason=agg_reason,
            evidence_source="Document Metadata",
            availability_status=agg_status,
        )
