"""
Safe Formatting Utilities for RAGGuard-TR.
Prevents format-string crashes when values are None, NaN, or Inf.
"""
import math
from typing import Any, Optional


def format_float(
    val: Optional[float],
    precision: int = 3,
    default: str = "N/A",
) -> str:
    """
    Safely format a float value to a fixed precision string.

    Returns `default` if `val` is None, NaN, or Infinite.
    """
    if val is None:
        return default
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f"{f_val:.{precision}f}"
    except (ValueError, TypeError):
        return default


def format_trri(trri: Optional[float], default: str = "N/A") -> str:
    """Format a TRRI score to 3 decimal places or return `default`."""
    return format_float(trri, precision=3, default=default)


def format_percent(val: Optional[float], precision: int = 1, default: str = "N/A") -> str:
    """Format a ratio [0.0, 1.0] as a percentage string (e.g. 85.5%)."""
    if val is None:
        return default
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f"{f_val * 100.0:.{precision}f}%"
    except (ValueError, TypeError):
        return default


def safe_format(template: str, **kwargs: Any) -> str:
    """
    Safely format a template string by pre-formatting float/None values.
    """
    processed = {}
    for k, v in kwargs.items():
        if isinstance(v, float) or v is None:
            processed[k] = format_float(v)
        else:
            processed[k] = str(v)
    try:
        return template.format(**processed)
    except Exception:
        return template
