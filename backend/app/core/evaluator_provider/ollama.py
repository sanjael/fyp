from .base import EvaluatorProvider, ProviderDeepEvalWrapper
from ..clients.langchain_adapter import OllamaChatAdapter
from ...core.config import global_config

class OllamaProvider(EvaluatorProvider):
    def __init__(self, model_name: str):
        super().__init__(model_name, rpm_limit=300)
        self.underlying_model = OllamaChatAdapter(model_name=model_name, base_url=global_config.OLLAMA_HOST)
        
    def get_langchain_model(self):
        return self.underlying_model
        
    def get_deepeval_model(self):
        # We don't need a heavy wrapper if we just want DeepEval's BaseLLM to work,
        # but our ProviderDeepEvalWrapper handles caching and metric logging.
        from .base import ProviderDeepEvalWrapper
        return ProviderDeepEvalWrapper(self)
        
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Open-source models running locally are essentially free
        return 0.0
