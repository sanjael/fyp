import pytest
from app.core.config import global_config

def test_config_loading():
    assert global_config.OLLAMA_HOST is not None
    assert global_config.EVALUATOR_PROVIDER in ("groq", "google", "ollama")
    assert isinstance(global_config.CHROMA_PORT, int)
