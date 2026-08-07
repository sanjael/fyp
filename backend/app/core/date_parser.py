"""
Hierarchical Temporal Resolver & Robust Date Parser for Document Metadata.
Supports ISO 8601, Unix timestamps (seconds/milliseconds), YYYY-MM-DD,
DOI/arXiv identifiers, IEEE/ACM publication lines, and 10-tier fallback logic.
"""
import re
import functools
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DOCUMENT_DATE_KEYS: List[str] = [
    "document_date",
    "date",
    "published_date",
    "publication_date",
    "publication_year",
    "created_at",
    "created_date",
    "timestamp",
    "doc_date",
    "year",
]


@functools.lru_cache(maxsize=1024)
def _cached_parse_year_or_date_str(val_str: str) -> Optional[int]:
    """Cached helper returning 4-digit year or None from raw strings."""
    if not val_str:
        return None
    val_clean = val_str.strip()
    match = re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", val_clean)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            pass
    return None


def parse_datetime(val: Any) -> Optional[datetime]:
    """
    Parses an arbitrary value into a UTC datetime object.
    """
    if val is None:
        return None

    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)

    if isinstance(val, (int, float)):
        if 1900 <= val <= 2100 and (isinstance(val, int) or val.is_integer()):
            return datetime(int(val), 1, 1, tzinfo=timezone.utc)
        return _from_numeric_timestamp(val)


    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("none", "null", "n/a", "unknown", ""):
        return None

    # Check 4-digit year string
    if re.match(r"^(19|20)\d{2}$", val_str):
        try:
            year = int(val_str)
            return datetime(year, 1, 1, tzinfo=timezone.utc)
        except ValueError:
            pass

    # Check numeric timestamp
    if val_str.isdigit() or re.match(r"^\d+\.\d+$", val_str):
        try:
            num = float(val_str)
            return _from_numeric_timestamp(num)
        except (ValueError, OverflowError):
            pass

    # ISO 8601 parsing
    try:
        clean_iso = val_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass

    # Regex YYYY-MM-DD
    match = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val_str)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            pass

    # Regex MM/DD/YYYY or DD-MM-YYYY
    match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})", val_str)
    if match:
        p1, p2, year = map(int, match.groups())
        for m, d in [(p1, p2), (p2, p1)]:
            try:
                return datetime(year, m, d, tzinfo=timezone.utc)
            except ValueError:
                continue

    return None


def _from_numeric_timestamp(val: float) -> Optional[datetime]:
    try:
        if val > 1e11:
            val /= 1000.0
        dt = datetime.fromtimestamp(val, tz=timezone.utc)
        return dt
    except (ValueError, OverflowError, OSError):
        return None


def extract_doc_datetime(metadata: Dict[str, Any], text_content: Optional[str] = None) -> Optional[datetime]:
    """
    10-Tier Hierarchical Temporal Resolver searching for authentic dates in order:
    1. PDF metadata keys
    2. First page title/header text
    3. Footer text
    4. DOI metadata string
    5. arXiv identifier (arXiv:YYMM.XXXXX)
    6. IEEE copyright line (© 20XX IEEE)
    7. ACM publication line (ACM 20XX)
    8. Filename regex matching (e.g. paper_2023.pdf)
    9. Embedded metadata strings
    10. Unknown -> Returns None (No constant substitution)
    """
    if not isinstance(metadata, dict):
        metadata = {}

    # Tier 1: Check document metadata keys
    for key in DOCUMENT_DATE_KEYS:
        val = metadata.get(key)
        if val is not None:
            parsed = parse_datetime(val)
            if parsed is not None:
                return parsed

    # Check text content for Tiers 2-7 if available
    if text_content:
        content_sample = text_content[:2000]

        # Tier 4: DOI metadata (e.g. 10.1145/2023...)
        doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", content_sample)
        if doi_match:
            year = _cached_parse_year_or_date_str(doi_match.group(0))
            if year:
                return datetime(year, 1, 1, tzinfo=timezone.utc)

        # Tier 5: arXiv ID (e.g. arXiv:2310.06825 -> YY=23 -> 2023)
        arxiv_match = re.search(r"arxiv:\s*(\d{2})(\d{2})\.\d+", content_sample, re.IGNORECASE)
        if arxiv_match:
            try:
                yy = int(arxiv_match.group(1))
                year = 2000 + yy if yy < 70 else 1900 + yy
                return datetime(year, 1, 1, tzinfo=timezone.utc)
            except ValueError:
                pass

        # Tier 6: IEEE copyright line (© 2024 IEEE or IEEE 2023)
        ieee_match = re.search(r"(?:©|copyright|\b) (19\d{2}|20\d{2}) \s*IEEE", content_sample, re.IGNORECASE)
        if ieee_match:
            try:
                return datetime(int(ieee_match.group(1)), 1, 1, tzinfo=timezone.utc)
            except ValueError:
                pass

        # Tier 7: ACM publication line (ACM 20XX)
        acm_match = re.search(r"ACM \s* (19\d{2}|20\d{2})", content_sample, re.IGNORECASE)
        if acm_match:
            try:
                return datetime(int(acm_match.group(1)), 1, 1, tzinfo=timezone.utc)
            except ValueError:
                pass

        # Tier 2 & 3: Header/Footer year pattern (19XX or 20XX)
        header_year = _cached_parse_year_or_date_str(content_sample)
        if header_year:
            return datetime(header_year, 1, 1, tzinfo=timezone.utc)

    # Tier 8: Filename regex matching (e.g., attention_is_all_you_need_2017.pdf)
    filename = str(metadata.get("filename", "") or metadata.get("document_filename", "") or "")
    if filename:
        year = _cached_parse_year_or_date_str(filename)
        if year:
            return datetime(year, 1, 1, tzinfo=timezone.utc)

    # Tier 9: Embedded metadata string search
    # Exclude internal bookkeeping fields that contain runtime timestamps
    # (e.g. ingestion_date, chunk_index) to prevent temporal leakage.
    _TIER9_EXCLUDE_KEYS = {
        "ingestion_date", "ingestion_timestamp", "ingest_time",
        "chunk_index", "chunk_id",
        "created_at", "updated_at", "modified_at",
        "filename", "document_filename",  # already handled by Tier 8
        "embedding_model", "collection_name",
    }
    filtered_meta = {k: v for k, v in metadata.items() if k not in _TIER9_EXCLUDE_KEYS}
    if filtered_meta:
        meta_str = str(filtered_meta)
        year = _cached_parse_year_or_date_str(meta_str)
        if year:
            return datetime(year, 1, 1, tzinfo=timezone.utc)

    # Tier 10: Unknown -> Returns None
    return None
