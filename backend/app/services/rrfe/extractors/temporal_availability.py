from typing import List

from langchain_core.documents import Document

from app.core.date_parser import extract_doc_datetime, _cached_parse_year_or_date_str
from ..core.base_extractor import BaseFeatureExtractor
from ..models import FeatureResult, TemporalAvailabilityResult


# Score assigned to each availability tier.
# Fixed by the RRFE scientific specification — do not alter without updating the
# methodology section of the accompanying paper.
_AVAILABILITY_SCORES = {
    "Available": 1.0,   # Tier-A: explicit publication metadata from source artifact
    "Estimated": 0.5,   # Tier-B: year inferred from document-origin text fields
    "Unknown":   0.0,   # Tier-C: no trustworthy temporal evidence found
}

# Tier-B: semantic metadata fields that originate FROM the source document (not the
# indexing pipeline).  A publication year extracted from any of these is an
# Estimated signal.
# NEVER add ingestion_date, chunk_index, created_at, updated_at, collection_name,
# embedding_model, or any field injected by chunk_document() — those are internal
# bookkeeping artifacts with no publication provenance.
_TIER_B_FIELDS = (
    "description", "abstract", "summary", "notes",
    "citation", "journal", "publisher",
)

# Confidence weights per tier used in the proportional aggregation formula.
_TIER_WEIGHTS = {
    "Available": 1.0,
    "Estimated": 0.5,
    "Unknown":   0.0,
}


class TemporalAvailabilityExtractor(BaseFeatureExtractor):
    """
    Measures whether retrieved documents contain trustworthy publication-time metadata.

    Three tiers (RRFE Temporal Availability specification):
      Tier-A  Available  (score=1.0) — explicit publication date from source artifact
      Tier-B  Estimated  (score=0.5) — year inferred from document-origin text fields
      Tier-C  Unknown    (score=0.0) — no trustworthy temporal evidence at all

    What NEVER counts as evidence:
      ingestion_date, ingestion_timestamp, chunk_index, created_at, updated_at,
      collection_name, embedding_model, or any field injected by the indexing
      pipeline.  These are runtime bookkeeping artifacts — they record when the
      system processed a document, not when the document was published.

    Confidence = weighted proportional mean across all retrieved chunks:
        confidence = mean(weight_i),  weight_i ∈ {1.0, 0.5, 0.0}

    This is SEPARATE from Temporal Freshness:
      Freshness    = how recent the document is (requires a known publication date)
      Availability = whether any trustworthy date exists at all
    """

    @property
    def feature_name(self) -> str:
        return "temporal_availability"

    def validate(self, query: str, docs: List[Document]) -> bool:
        return bool(docs)

    def _classify_doc(self, doc: Document) -> tuple[str, str]:
        """
        Classify a single chunk into a temporal availability tier.
        Returns (status, reason) where status ∈ {"Available", "Estimated", "Unknown"}.
        """
        meta = doc.metadata

        # ------------------------------------------------------------------
        # Tier-A: extract_doc_datetime() resolved an explicit publication date
        # from structured metadata keys (publication_date, published_date, etc.),
        # DOI, arXiv ID, IEEE/ACM copyright line, or filename year.
        # All Tier-9 internal keys (ingestion_date, chunk_index, etc.) are
        # already filtered inside extract_doc_datetime() — see date_parser.py.
        # ------------------------------------------------------------------
        parsed_dt = extract_doc_datetime(meta)
        if parsed_dt is not None:
            return (
                "Available",
                f"Explicit publication date ({parsed_dt.strftime('%Y-%m-%d')}) "
                f"found in document metadata (Tier-A evidence)",
            )

        # ------------------------------------------------------------------
        # Tier-B: Attempt year extraction from document-origin semantic fields.
        # These fields originate from the source document and may embed a
        # publication year (e.g., "Published in NEJM, 2022").
        # ingestion_date is explicitly NOT checked here — it is a pipeline
        # artifact, not a publication provenance signal.
        # ------------------------------------------------------------------
        for field in _TIER_B_FIELDS:
            val = meta.get(field)
            if val:
                year = _cached_parse_year_or_date_str(str(val))
                if year:
                    return (
                        "Estimated",
                        f"Publication year {year} inferred from '{field}' field "
                        f"(Tier-B evidence; document-origin text, not verified against "
                        f"structured metadata)",
                    )

        # Tier-B fallback: scan the first 500 characters of the document body.
        # Mirrors the header/footer heuristic in date_parser Tiers 2–3.
        if doc.page_content:
            year = _cached_parse_year_or_date_str(doc.page_content[:500])
            if year:
                return (
                    "Estimated",
                    f"Publication year {year} inferred from document body text "
                    f"(Tier-B header/footer heuristic; not verified against structured "
                    f"metadata)",
                )

        # ------------------------------------------------------------------
        # Tier-C: No trustworthy temporal evidence found.
        # Unknown is a scientifically valid outcome — the retrieval system
        # cannot verify the temporal provenance of this chunk.
        # ------------------------------------------------------------------
        return (
            "Unknown",
            "No trustworthy temporal evidence found in document metadata or body "
            "(ingestion timestamps excluded from evidence)",
        )

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

        # ------------------------------------------------------------------
        # Aggregation:
        #   Score      = maximum (best available provenance tier across chunks)
        #   Confidence = proportional weighted mean across all chunks
        #                confidence = mean(weight_i) ∈ [0, 1]
        #
        # A single chunk with an explicit publication date elevates the query's
        # temporal availability score to 1.0, while confidence correctly reflects
        # how densely temporal evidence is distributed across the retrieved set.
        # ------------------------------------------------------------------
        confidence = sum(_TIER_WEIGHTS[s] for s in status_values) / len(status_values)

        if "Available" in status_values:
            agg_status = "Available"
            available_count = status_values.count("Available")
            agg_reason = (
                f"{available_count}/{len(docs)} chunks have explicit publication date "
                f"(Tier-A evidence)"
            )
        elif "Estimated" in status_values:
            agg_status = "Estimated"
            est_count = status_values.count("Estimated")
            agg_reason = (
                f"{est_count}/{len(docs)} chunks have inferred publication year "
                f"(Tier-B evidence; no explicit publication date found)"
            )
        else:
            agg_status = "Unknown"
            agg_reason = (
                "No trustworthy temporal evidence in any retrieved chunk "
                "(Tier-C; ingestion timestamps excluded)"
            )

        score = _AVAILABILITY_SCORES[agg_status]

        return TemporalAvailabilityResult(
            score=round(score, 4),
            confidence=round(confidence, 4),
            reason=agg_reason,
            evidence_source="Document Metadata / Body Text",
            availability_status=agg_status,
        )
