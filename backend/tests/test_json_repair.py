import pytest
from app.core.json_repair import clean_json_text, parse_and_repair_json

def test_clean_json_text_markdown():
    raw = "```json\n{\n  \"score\": 0.95,\n  \"reason\": \"supported\"\n}\n```"
    cleaned = clean_json_text(raw)
    assert cleaned == '{\n  "score": 0.95,\n  "reason": "supported"\n}'

def test_clean_json_text_trailing_commas():
    raw = '{"score": 0.85, "verdict": "yes",}'
    cleaned = clean_json_text(raw)
    assert cleaned == '{"score": 0.85, "verdict": "yes"}'

def test_parse_and_repair_json_valid():
    raw = "```json\n{\"faithfulness\": 0.9}\n```"
    res = parse_and_repair_json(raw)
    assert isinstance(res, dict)
    assert res.get("faithfulness") == 0.9
