"""
Robust Date & Timestamp Parser for Document Metadata.
Supports ISO 8601, Unix timestamps (seconds/milliseconds), YYYY-MM-DD,
YYYY/MM/DD, year-only strings, and timezone normalization to UTC.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Standard document date metadata keys to inspect in priority order
DOCUMENT_DATE_KEYS: List[str] = [
    "document_date",
    "date",
    "published_date",
    "publication_date",
    "created_at",
    "created_date",
    "timestamp",
    "doc_date",
    "year",
]


def parse_datetime(val: Any) -> Optional[datetime]:
    """
    Parses an arbitrary value into a UTC datetime object.

    Supported inputs:
      - datetime object
      - numeric timestamp (int/float, seconds or milliseconds)
      - numeric string timestamp ("1690000000")
      - ISO 8601 string ("2023-10-12T14:30:00Z", "2023-10-12T14:30:00+00:00")
      - YYYY-MM-DD / YYYY/MM/DD / MM/DD/YYYY / DD-MM-YYYY
      - 4-digit Year string ("2023" -> 2023-01-01 00:00:00 UTC)
    """
    if val is None:
        return None

    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)

    # Convert numeric types (int/float) to timestamp
    if isinstance(val, (int, float)):
        return _from_numeric_timestamp(val)

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("none", "null", "n/a", "unknown", ""):
        return None

    # Check if string is a 4-digit year (e.g. "2023")
    if re.match(r"^(19|20)\d{2}$", val_str):
        try:
            year = int(val_str)
            return datetime(year, 1, 1, tzinfo=timezone.utc)
        except ValueError:
            pass

    # Check if string is a numeric timestamp
    if val_str.isdigit() or re.match(r"^\d+\.\d+$", val_str):
        try:
            num = float(val_str)
            return _from_numeric_timestamp(num)
        except (ValueError, OverflowError):
            pass

    # Standard ISO 8601 parsing
    try:
        clean_iso = val_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass

    # Regex date formats
    # 1. YYYY-MM-DD or YYYY/MM/DD
    match = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val_str)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            pass

    # 2. MM/DD/YYYY or DD-MM-YYYY
    match = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})", val_str)
    if match:
        p1, p2, year = map(int, match.groups())
        # Try MM/DD/YYYY first, fallback to DD/MM/YYYY
        for m, d in [(p1, p2), (p2, p1)]:
            try:
                return datetime(year, m, d, tzinfo=timezone.utc)
            except ValueError:
                continue

    # 3. Year only ("2023")
    match = re.match(r"^(19|20)\d{2}$", val_str)
    if match:
        year = int(val_str)
        return datetime(year, 1, 1, tzinfo=timezone.utc)

    return None


def _from_numeric_timestamp(val: float) -> Optional[datetime]:
    """Helper to convert numeric timestamp in seconds or milliseconds."""
    try:
        # If timestamp is in milliseconds (greater than year 3000 in seconds)
        if val > 1e11:
            val /= 1000.0
        dt = datetime.fromtimestamp(val, tz=timezone.utc)
        return dt
    except (ValueError, OverflowError, OSError):
        return None


def extract_doc_datetime(metadata: Dict[str, Any]) -> Optional[datetime]:
    """
    Inspects document metadata for known date keys and parses the first valid value.
    """
    if not isinstance(metadata, dict):
        return None

    for key in DOCUMENT_DATE_KEYS:
        val = metadata.get(key)
        if val is not None:
            parsed = parse_datetime(val)
            if parsed is not None:
                return parsed

    # Secondary heuristic: extract 4-digit year from filename if present
    filename = str(metadata.get("filename", "") or metadata.get("document_filename", "") or "")
    if filename:
        match = re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", filename)
        if match:
            try:
                year = int(match.group(0))
                return datetime(year, 1, 1, tzinfo=timezone.utc)
            except ValueError:
                pass

    return None
