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
