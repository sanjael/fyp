from .base import EvaluatorProvider, ProviderDeepEvalWrapper
from ..clients.langchain_adapter import GroqChatAdapter
from ...core.config import global_config

class GroqProvider(EvaluatorProvider):
    def __init__(self, model_name: str):
        super().__init__(model_name, rpm_limit=30) # Groq has strict rate limits
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
