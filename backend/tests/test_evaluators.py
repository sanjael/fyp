import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

# Mock dependencies before importing the wrappers to avoid library missing errors in test environment
import sys
sys.modules['datasets'] = MagicMock()
sys.modules['ragas'] = MagicMock()
sys.modules['ragas.metrics'] = MagicMock()
sys.modules['deepeval'] = MagicMock()
sys.modules['deepeval.metrics'] = MagicMock()
sys.modules['deepeval.test_case'] = MagicMock()
sys.modules['deepeval.models.base_model'] = MagicMock()

from app.services.dataset_construction.evaluators.ragas_wrapper import RagasWrapper, RAGAS_AVAILABLE
from app.services.dataset_construction.evaluators.deepeval_wrapper import DeepEvalWrapper, DEEPEVAL_AVAILABLE

def test_ragas_wrapper_unavailable():
    """Test graceful failure when Ragas is not available."""
    with patch('app.services.dataset_construction.evaluators.ragas_wrapper.RAGAS_AVAILABLE', False):
        wrapper = RagasWrapper()
        doc = Document(page_content="test", metadata={})
        result = wrapper.compute_metrics("q", "a", [doc])
        assert result == {}

def test_deepeval_wrapper_unavailable():
    """Test graceful failure when DeepEval is not available."""
    with patch('app.services.dataset_construction.evaluators.deepeval_wrapper.DEEPEVAL_AVAILABLE', False):
        wrapper = DeepEvalWrapper()
        doc = Document(page_content="test", metadata={})
        result = wrapper.compute_metrics("q", "a", [doc])
        assert result == {}

# Note: Integration tests requiring the real Ollama instance and Ragas library
# will be executed in the Docker environment during the pipeline run.
