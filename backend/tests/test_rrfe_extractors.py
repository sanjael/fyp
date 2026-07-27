"""
Unit tests for all RRFE feature extractors.
Run with:  pytest backend/tests/test_rrfe_extractors.py -v
"""
import math
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from app.services.rrfe.models import FeatureResult, TemporalAvailabilityResult
from app.services.rrfe.extractors.temporal_freshness import TemporalFreshnessExtractor
from app.services.rrfe.extractors.temporal_availability import TemporalAvailabilityExtractor
from app.services.rrfe.extractors.source_credibility import SourceCredibilityExtractor
from app.services.rrfe.extractors.evidence_consistency import EvidenceConsistencyExtractor
from app.services.rrfe.extractors.evidence_sufficiency import EvidenceSufficiencyExtractor
from app.services.rrfe.config import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc(content: str = "text", **meta) -> Document:
    return Document(page_content=content, metadata=meta)


def _iso(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# Temporal Freshness
# ---------------------------------------------------------------------------

class TestTemporalFreshnessExtractor:
    ext = TemporalFreshnessExtractor()

    def test_returns_feature_result(self):
        doc = _doc(document_date=_iso(0))
        result = self.ext.extract("q", [doc])
        assert isinstance(result, FeatureResult)

    def test_score_at_zero_days_is_one(self):
        doc = _doc(document_date=_iso(0))
        result = self.ext.extract("q", [doc])
        assert result.score == pytest.approx(1.0, abs=0.01)
        assert result.confidence == 1.0

    def test_score_at_half_life_is_half(self):
        doc = _doc(document_date=_iso(180))
        result = self.ext.extract("q", [doc])
        assert result.score == pytest.approx(0.5, abs=0.02)

    def test_score_at_360_days_is_quarter(self):
        doc = _doc(document_date=_iso(360))
        result = self.ext.extract("q", [doc])
        assert result.score == pytest.approx(0.25, abs=0.02)

    def test_no_document_date_returns_none_score(self):
        doc = _doc(ingestion_date=_iso(0))   # ingestion_date must NOT be used
        result = self.ext.extract("q", [doc])
        assert result.confidence == 0.0
        assert result.score is None
        assert "No document_date" in result.reason
        assert result.evidence_source == "Unavailable"

    def test_empty_docs_returns_none_score(self):
        result = self.ext.extract("q", [])
        assert result.confidence == 0.0
        assert result.score is None
        assert result.evidence_source == "Unavailable"

    def test_partial_dates_confidence_scales(self):
        docs = [_doc(document_date=_iso(10)), _doc()]  # 1 of 2 has date
        result = self.ext.extract("q", docs)
        assert result.confidence == pytest.approx(0.5, abs=0.01)

    def test_score_never_exceeds_one(self):
        doc = _doc(document_date=_iso(0))
        result = self.ext.extract("q", [doc])
        assert result.score <= 1.0

    def test_score_never_below_zero(self):
        doc = _doc(document_date=_iso(10000))
        result = self.ext.extract("q", [doc])
        assert result.score >= 0.0

    def test_ingestion_date_not_used_as_fallback(self):
        """ingestion_date is always recent — must never inflate freshness."""
        doc = _doc(ingestion_date=_iso(0))
        result = self.ext.extract("q", [doc])
        assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Temporal Availability
# ---------------------------------------------------------------------------

class TestTemporalAvailabilityExtractor:
    ext = TemporalAvailabilityExtractor()

    def test_returns_temporal_availability_result(self):
        doc = _doc(document_date=_iso(10))
        result = self.ext.extract("q", [doc])
        assert isinstance(result, TemporalAvailabilityResult)

    def test_available_when_document_date_present(self):
        doc = _doc(document_date=_iso(10))
        result = self.ext.extract("q", [doc])
        assert result.availability_status == "Available"
        assert result.score == 1.0
        assert result.confidence == 1.0

    def test_estimated_when_only_ingestion_date(self):
        doc = _doc(ingestion_date=_iso(0))
        result = self.ext.extract("q", [doc])
        assert result.availability_status == "Estimated"
        assert result.score == 0.5

    def test_estimated_when_year_in_filename(self):
        doc = _doc(filename="report_2023_annual.pdf")
        result = self.ext.extract("q", [doc])
        assert result.availability_status == "Estimated"

    def test_unknown_when_no_date_signal(self):
        doc = _doc()
        result = self.ext.extract("q", [doc])
        assert result.availability_status == "Unknown"
        assert result.score == 0.0
        assert result.confidence == 0.0

    def test_available_takes_priority_over_estimated(self):
        docs = [_doc(document_date=_iso(5)), _doc(ingestion_date=_iso(0))]
        result = self.ext.extract("q", docs)
        assert result.availability_status == "Available"

    def test_empty_docs(self):
        result = self.ext.extract("q", [])
        assert result.availability_status == "Unknown"
        # TemporalAvailability: score=0.0 for Unknown is a legitimate calculated value
        assert result.score == 0.0
        assert result.confidence == 0.0

    def test_freshness_and_availability_are_independent(self):
        """Availability score must not depend on document age."""
        old_doc = _doc(document_date=_iso(3000))
        new_doc = _doc(document_date=_iso(1))
        r_old = self.ext.extract("q", [old_doc])
        r_new = self.ext.extract("q", [new_doc])
        # Both have document_date → both Available → same score
        assert r_old.availability_status == "Available"
        assert r_new.availability_status == "Available"
        assert r_old.score == r_new.score


# ---------------------------------------------------------------------------
# Source Credibility
# ---------------------------------------------------------------------------

class TestSourceCredibilityExtractor:
    ext = SourceCredibilityExtractor()

    def test_returns_feature_result(self):
        doc = _doc(document_type="academic_paper")
        result = self.ext.extract("q", [doc])
        assert isinstance(result, FeatureResult)

    def test_academic_paper_high_score(self):
        doc = _doc(document_type="academic_paper", document_date=_iso(10))
        result = self.ext.extract("q", [doc])
        assert result.score >= 0.90

    def test_blog_post_low_score(self):
        doc = _doc(document_type="blog_post")
        result = self.ext.extract("q", [doc])
        assert result.score < 0.50

    def test_social_media_lowest_score(self):
        doc = _doc(document_type="social_media")
        result = self.ext.extract("q", [doc])
        assert result.score <= 0.25

    def test_doi_bonus_applied(self):
        base = _doc(document_type="academic_paper", document_date=_iso(10))
        with_doi = _doc(document_type="academic_paper", doi="10.1234/test", document_date=_iso(10))
        r_base = self.ext.extract("q", [base])
        r_doi = self.ext.extract("q", [with_doi])
        assert r_doi.score > r_base.score

    def test_trusted_domain_bonus(self):
        doc_plain = _doc(document_type="news_article")
        doc_gov = _doc(document_type="news_article", source_url="https://cdc.gov/report")
        r_plain = self.ext.extract("q", [doc_plain])
        r_gov = self.ext.extract("q", [doc_gov])
        assert r_gov.score > r_plain.score

    def test_missing_date_penalty(self):
        with_date = _doc(document_type="news_article", document_date=_iso(10))
        no_date = _doc(document_type="news_article")
        r_with = self.ext.extract("q", [with_date])
        r_no = self.ext.extract("q", [no_date])
        assert r_with.score > r_no.score

    def test_precomputed_credibility_used_directly(self):
        doc = _doc(estimated_credibility=0.77)
        result = self.ext.extract("q", [doc])
        assert result.score == pytest.approx(0.77, abs=0.001)

    def test_reason_is_never_empty(self):
        doc = _doc()
        result = self.ext.extract("q", [doc])
        assert len(result.reason) > 0

    def test_confidence_zero_for_all_unknown_types(self):
        doc = _doc(document_type="unknown")
        result = self.ext.extract("q", [doc])
        assert result.confidence == 0.0

    def test_empty_docs_returns_none_score(self):
        result = self.ext.extract("q", [])
        assert result.confidence == 0.0
        assert result.score is None
        assert result.evidence_source == "Unavailable"


# ---------------------------------------------------------------------------
# Evidence Consistency
# ---------------------------------------------------------------------------

class TestEvidenceConsistencyExtractor:

    def _make_extractor_with_mock(self, embed_return):
        ext = EvidenceConsistencyExtractor()
        mock_emb = MagicMock()
        mock_emb.embed_documents.return_value = embed_return
        import app.services.rrfe.extractors.evidence_consistency as mod
        mod.embeddings = mock_emb
        return ext

    def test_returns_feature_result(self):
        import numpy as np
        vecs = [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
        ext = self._make_extractor_with_mock(vecs)
        docs = [_doc("a"), _doc("b"), _doc("c")]
        result = ext.extract("q", docs)
        assert isinstance(result, FeatureResult)

    def test_identical_chunks_high_consistency(self):
        import numpy as np
        vecs = [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
        ext = self._make_extractor_with_mock(vecs)
        docs = [_doc("a"), _doc("b"), _doc("c")]
        result = ext.extract("q", docs)
        assert result.score >= 0.8

    def test_orthogonal_chunks_low_consistency(self):
        vecs = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        ext = self._make_extractor_with_mock(vecs)
        docs = [_doc("a"), _doc("b"), _doc("c")]
        result = ext.extract("q", docs)
        assert result.score < 0.5

    def test_single_doc_returns_none_score(self):
        ext = EvidenceConsistencyExtractor()
        result = ext.extract("q", [_doc("only one")])
        assert result.confidence == 0.0
        assert result.score is None
        assert result.evidence_source == "Unavailable"

    def test_reason_contains_variance(self):
        import numpy as np
        vecs = [[1, 0, 0], [0, 1, 0]]
        ext = self._make_extractor_with_mock(vecs)
        docs = [_doc("a"), _doc("b")]
        result = ext.extract("q", docs)
        assert "variance" in result.reason.lower()


# ---------------------------------------------------------------------------
# Evidence Sufficiency
# ---------------------------------------------------------------------------

class TestEvidenceSufficiencyExtractor:

    def _make_extractor_with_mock(self, query_vec, doc_vecs):
        ext = EvidenceSufficiencyExtractor()
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = query_vec
        mock_emb.embed_documents.return_value = doc_vecs
        import app.services.rrfe.extractors.evidence_sufficiency as mod
        mod.embeddings = mock_emb
        return ext

    def test_returns_feature_result(self):
        ext = self._make_extractor_with_mock([1, 0, 0], [[1, 0, 0], [1, 0, 0]])
        result = ext.extract("q", [_doc("a"), _doc("b")])
        assert isinstance(result, FeatureResult)

    def test_perfect_match_high_score(self):
        ext = self._make_extractor_with_mock([1, 0, 0], [[1, 0, 0], [1, 0, 0]])
        result = ext.extract("q", [_doc("a"), _doc("b")])
        assert result.score >= 0.9

    def test_no_match_low_score(self):
        ext = self._make_extractor_with_mock([1, 0, 0], [[0, 1, 0], [0, 0, 1]])
        result = ext.extract("q", [_doc("a"), _doc("b")])
        assert result.score < 0.3

    def test_score_uses_weighted_max_mean(self):
        """score = 0.6*max + 0.4*mean — verify formula directly."""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        q = [1, 0, 0]
        d = [[1, 0, 0], [0, 1, 0]]   # sims = [1.0, 0.0]
        ext = self._make_extractor_with_mock(q, d)
        result = ext.extract("q", [_doc("a"), _doc("b")])
        expected = 0.6 * 1.0 + 0.4 * 0.5
        assert result.score == pytest.approx(expected, abs=0.02)

    def test_reason_contains_coverage(self):
        ext = self._make_extractor_with_mock([1, 0, 0], [[1, 0, 0], [1, 0, 0]])
        result = ext.extract("q", [_doc("a"), _doc("b")])
        assert "coverage" in result.reason.lower()

    def test_empty_docs_returns_none_score(self):
        ext = EvidenceSufficiencyExtractor()
        result = ext.extract("q", [])
        assert result.confidence == 0.0
        assert result.score is None
        assert result.evidence_source == "Unavailable"

    def test_score_bounded(self):
        ext = self._make_extractor_with_mock([1, 0, 0], [[1, 0, 0]])
        result = ext.extract("q", [_doc("a")])
        assert 0.0 <= result.score <= 1.0
