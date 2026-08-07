from .base import EvaluatorProvider, ProviderDeepEvalWrapper
from ..clients.langchain_adapter import GroqChatAdapter
from ...core.config import global_config

import logging

logger = logging.getLogger("evaluator_provider.groq")

class GroqProvider(EvaluatorProvider):
    def __init__(self, model_name: str):
        super().__init__(
            model_name=model_name,
            rpm_limit=30,
            tpm_limit=5000,
            max_concurrency=global_config.EVALUATOR_CONCURRENCY,
            max_retries=global_config.EVALUATOR_MAX_RETRIES,
            max_wait=global_config.EVALUATOR_MAX_WAIT,
            timeout=global_config.EVALUATOR_TIMEOUT,
        )
        logger.info(
            f"Initialized GroqProvider [model={model_name}, max_concurrency={self.max_concurrency}, "
            f"max_retries={self.max_retries}, max_wait={self.max_wait}s, timeout={self.timeout}s]"
        )
        self.underlying_model = GroqChatAdapter(
            model_name=model_name, 
            api_key=global_config.GROQ_API_KEY
        )

        
    def get_langchain_model(self):
        return self.underlying_model
        
    def get_deepeval_model(self):
        return ProviderDeepEvalWrapper(self)
        
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Approximate cost for Groq Llama 3 models
        if "8b" in self.model_name.lower():
            return (prompt_tokens * 0.05 / 1e6) + (completion_tokens * 0.08 / 1e6)
        return (prompt_tokens * 0.59 / 1e6) + (completion_tokens * 0.79 / 1e6)
