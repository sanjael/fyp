"""
JSON Repair and Output Cleaning Utility.
Ensures LLM responses (from DeepEval, RAGAS, or custom models) are parsed
robustly, stripping markdown backticks, trailing commas, and repairing malformed syntax.
"""
import json
import re
from typing import Any, Dict, List, Optional, Union


def clean_json_text(text: str) -> str:
    """
    Strips markdown code blocks, lead/tail whitespace, and extracts the primary
    JSON block from raw LLM output text.
    """
    if not text:
        return ""

    cleaned = text.strip()

    # 1. Remove markdown backtick blocks ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    # 2. Extract content between first '{' or '[' and last '}' or ']'
    start_brace = cleaned.find("{")
    start_bracket = cleaned.find("[")

    if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
        end_brace = cleaned.rfind("}")
        if end_brace != -1 and end_brace > start_brace:
            cleaned = cleaned[start_brace : end_brace + 1]
    elif start_bracket != -1:
        end_bracket = cleaned.rfind("]")
        if end_bracket != -1 and end_bracket > start_bracket:
            cleaned = cleaned[start_bracket : end_bracket + 1]

    # 3. Clean up trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    return cleaned


def parse_and_repair_json(text: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Parses a string into a JSON dictionary or list.
    Applies text cleaning and syntax repair fallback algorithms.
    Raises ValueError if parsing fails.
    """
    if not text or not text.strip():
        raise ValueError("Empty text provided for JSON parsing")

    # Attempt 1: Direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: Cleaned JSON text parsing
    cleaned = clean_json_text(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 3: Common fixes (unescaped newlines inside strings, single to double quotes)
    repaired = cleaned.replace("'", '"')
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM JSON output after repairs. Raw text snippet: {text[:200]!r}") from exc
