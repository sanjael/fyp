import pytest
from datetime import datetime, timezone
from app.core.date_parser import parse_datetime, extract_doc_datetime

def test_parse_datetime_iso():
    dt = parse_datetime("2023-10-12T14:30:00Z")
    assert dt is not None
    assert dt.year == 2023
    assert dt.month == 10
    assert dt.day == 12
    assert dt.tzinfo == timezone.utc

def test_parse_datetime_standard_date():
    dt = parse_datetime("2023-05-18")
    assert dt is not None
    assert dt.year == 2023
    assert dt.month == 5
    assert dt.day == 18

def test_parse_datetime_unix_timestamp():
    dt = parse_datetime(1690000000)
    assert dt is not None
    assert dt.year == 2023

def test_parse_datetime_year_only():
    dt = parse_datetime("2022")
    assert dt is not None
    assert dt.year == 2022
    assert dt.month == 1

def test_extract_doc_datetime_metadata_keys():
    meta = {"published_date": "2023-11-20T00:00:00Z"}
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt.year == 2023
    assert dt.month == 11

def test_extract_doc_datetime_filename_fallback():
    meta = {"filename": "paper_2021_v2.pdf"}
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt.year == 2021


# ---------------------------------------------------------------------------
# Regression tests: Tier 9 temporal leakage fix
# ---------------------------------------------------------------------------

def test_tier9_ingestion_date_only_returns_none():
    """Case 1: Metadata with only internal fields must NOT leak ingestion_date year."""
    meta = {
        "filename": "eval_doc.txt",
        "chunk_index": 0,
        "ingestion_date": "2026-08-06T09:30:00.123456",
    }
    dt = extract_doc_datetime(meta)
    assert dt is None, (
        f"Expected None when only ingestion_date is present, got {dt}"
    )


def test_tier9_publication_date_still_works():
    """Case 2: Explicit publication_date must still be resolved (Tier 1)."""
    meta = {
        "filename": "eval_doc.txt",
        "chunk_index": 0,
        "ingestion_date": "2026-08-06T09:30:00",
        "publication_date": "2019-03-15",
    }
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt.year == 2019
    assert dt.month == 3
    assert dt.day == 15


def test_tier9_description_field_extracts_year():
    """Case 3: Legitimate metadata field 'description' should still be parsed by Tier 9."""
    meta = {
        "filename": "eval_doc.txt",
        "chunk_index": 0,
        "ingestion_date": "2026-08-06T09:30:00",
        "description": "The paper was published in 2022.",
    }
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt.year == 2022


def test_tier9_publication_date_preferred_over_ingestion():
    """Case 4: When both ingestion_date and publication_date exist, publication_date wins."""
    meta = {
        "filename": "eval_doc.txt",
        "chunk_index": 0,
        "ingestion_date": "2026-08-06T09:30:00",
        "publication_date": "2019-01-01",
    }
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt.year == 2019, (
        f"Expected publication year 2019, got {dt.year} (possible ingestion_date leakage)"
    )


def test_tier9_sample_id_with_no_year_returns_none():
    """Edge case: sample_id containing hex/numeric should not be misinterpreted as a year."""
    meta = {
        "filename": "eval_doc.txt",
        "chunk_index": 0,
        "ingestion_date": "2026-08-06T09:30:00",
        "sample_id": "5abe65e25542993f32c2a101",
    }
    dt = extract_doc_datetime(meta)
    assert dt is None


# ---------------------------------------------------------------------------
# Regression tests: Integer-year date parsing P0 fix
# ---------------------------------------------------------------------------

def test_regression_parse_datetime_int_year():
    """Test 1: parse_datetime(2024) returns 2024-01-01 (not 1970 Unix timestamp)."""
    dt = parse_datetime(2024)
    assert dt is not None
    assert dt == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_regression_parse_datetime_float_year():
    """Test 2: parse_datetime(2024.0) returns 2024-01-01."""
    dt = parse_datetime(2024.0)
    assert dt is not None
    assert dt == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_regression_parse_datetime_unix_timestamp_preserved():
    """Test 3: parse_datetime(1715900000) converts as Unix timestamp (2024-05-16)."""
    dt = parse_datetime(1715900000)
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 5



def test_regression_extract_doc_datetime_publication_year():
    """Test 4: extract_doc_datetime({"publication_year": 2024}) returns 2024-01-01."""
    meta = {"publication_year": 2024}
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_regression_extract_doc_datetime_year_key():
    """Test 5: extract_doc_datetime({"year": 2024}) returns 2024-01-01."""
    meta = {"year": 2024}
    dt = extract_doc_datetime(meta)
    assert dt is not None
    assert dt == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_regression_temporal_freshness_non_zero_for_2024():
    """Test 6: Temporal Freshness score for a 2024 document is non-zero (0.026), not 0.0000."""
    from langchain_core.documents import Document
    from app.services.rrfe.extractors.temporal_freshness import TemporalFreshnessExtractor
    
    ext = TemporalFreshnessExtractor()
    doc = Document(
        page_content="Medical study",
        metadata={"filename": "pubmed_doc.txt", "publication_year": 2024, "ingestion_date": "2026-08-06T00:00:00"}
    )
    result = ext.extract("query", [doc])
    assert result.score is not None
    assert result.score > 0.0, f"Expected non-zero freshness for 2024 doc, got {result.score}"
    assert result.score == 0.026



def test_regression_temporal_availability_no_1970_false_positive():
    """Test 7: Temporal Availability correctly identifies Tier-A Available date for 2024-01-01 (not 1970)."""
    from langchain_core.documents import Document
    from app.services.rrfe.extractors.temporal_availability import TemporalAvailabilityExtractor
    
    ext = TemporalAvailabilityExtractor()
    doc = Document(
        page_content="Medical study",
        metadata={"filename": "pubmed_doc.txt", "publication_year": 2024, "ingestion_date": "2026-08-06T00:00:00"}
    )
    result = ext.extract("query", [doc])
    assert result.availability_status == "Available"
    assert "Tier-A evidence" in result.reason
    assert "1970" not in result.reason


