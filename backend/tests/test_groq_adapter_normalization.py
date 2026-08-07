import json
import pytest
from app.core.clients.langchain_adapter import GroqChatAdapter

def get_adapter():
    return GroqChatAdapter(model_name="llama-3.3-70b-versatile", api_key="test_key")

def test_verdict_integer():
    adapter = get_adapter()
    raw = json.dumps([{"reason": "valid statement", "verdict": 1}])
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, list)
    assert data[0]["verdict"] == 1

def test_verdict_string():
    adapter = get_adapter()
    raw = json.dumps([{"reason": "valid statement", "verdict": "1"}])
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, list)
    assert data[0]["verdict"] == 1

def test_yes_no_conversion():
    adapter = get_adapter()
    raw_yes = json.dumps([{"reason": "statement 1", "verdict": "yes"}])
    raw_no = json.dumps([{"reason": "statement 2", "verdict": "no"}])
    
    data_yes = json.loads(adapter._normalize_json_response(raw_yes))
    data_no = json.loads(adapter._normalize_json_response(raw_no))
    
    assert data_yes[0]["verdict"] == 1
    assert data_no[0]["verdict"] == 0

def test_true_false_conversion():
    adapter = get_adapter()
    raw_true = json.dumps([{"reason": "statement 1", "verdict": "true"}])
    raw_false = json.dumps([{"reason": "statement 2", "verdict": "false"}])
    
    data_true = json.loads(adapter._normalize_json_response(raw_true))
    data_false = json.loads(adapter._normalize_json_response(raw_false))
    
    assert data_true[0]["verdict"] == 1
    assert data_false[0]["verdict"] == 0

def test_wrapped_dict_and_statement_rename():
    adapter = get_adapter()
    raw = json.dumps({"statement_1": "School name", "reason": "Not specified", "verdict": "-1"})
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["statement"] == "School name"
    assert data[0]["verdict"] == -1
    assert data[0]["reason"] == "Not specified"

def test_wrapped_statements_list_and_rename():
    adapter = get_adapter()
    raw = json.dumps([
        {"statement_1": "ABC", "reason": "r1", "verdict": "0"},
        {"statement_2": "DEF", "reason": "r2", "verdict": "1"}
    ])
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["statement"] == "ABC"
    assert data[0]["verdict"] == 0
    assert data[1]["statement"] == "DEF"
    assert data[1]["verdict"] == 1

def test_preserve_statement_generation():
    adapter = get_adapter()
    raw = json.dumps({"statements": ["Statement 1", "Statement 2"]})
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, dict)
    assert data["statements"] == ["Statement 1", "Statement 2"]

def test_preserve_noncommittal_question():
    adapter = get_adapter()
    raw = json.dumps({"question": "What is Einstein famous for?", "noncommittal": 1})
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, dict)
    assert data["question"] == "What is Einstein famous for?"
    assert data["noncommittal"] == 1

def test_already_valid_list():
    adapter = get_adapter()
    raw = json.dumps([
        {"statement": "S1", "reason": "R1", "verdict": 1},
        {"statement": "S2", "reason": "R2", "verdict": 0}
    ])
    normalized = adapter._normalize_json_response(raw)
    data = json.loads(normalized)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["verdict"] == 1
    assert data[1]["verdict"] == 0

def test_malformed_json():
    adapter = get_adapter()
    raw = "Malformed output from LLM without JSON formatting"
    normalized = adapter._normalize_json_response(raw)
    assert normalized == raw
