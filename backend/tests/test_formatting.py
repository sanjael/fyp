import math
import pytest
from app.core.formatting import format_float, format_trri, format_percent, safe_format

def test_format_float_valid():
    assert format_float(0.92345) == "0.923"
    assert format_float(0.92345, precision=2) == "0.92"
    assert format_float(0.0) == "0.000"
    assert format_float(1.0) == "1.000"

def test_format_float_none_and_nan():
    assert format_float(None) == "N/A"
    assert format_float(None, default="Missing") == "Missing"
    assert format_float(float("nan")) == "N/A"
    assert format_float(float("inf")) == "N/A"

def test_format_trri():
    assert format_trri(0.8512) == "0.851"
    assert format_trri(None) == "N/A"

def test_format_percent():
    assert format_percent(0.855) == "85.5%"
    assert format_percent(1.0) == "100.0%"
    assert format_percent(None) == "N/A"

def test_safe_format():
    res = safe_format("TRRI={trri}, score={score}, name={name}", trri=0.912, score=None, name="test")
    assert "TRRI=0.912" in res
    assert "score=N/A" in res
    assert "name=test" in res
