from .base import EvaluatorProvider
from langchain_google_genai import ChatGoogleGenerativeAI
from ...core.config import global_config

class GeminiProvider(EvaluatorProvider):
    def __init__(self, model_name: str, rpm_limit: int = 15): # Gemini 15 RPM free tier default
        super().__init__(model_name, rpm_limit)
        self.underlying_model = ChatGoogleGenerativeAI(
            model=model_name, 
            google_api_key=global_config.GOOGLE_API_KEY
        )
        
    def get_langchain_model(self):
        return self.underlying_model
        
    def get_deepeval_model(self):
        from .base import ProviderDeepEvalWrapper
        return ProviderDeepEvalWrapper(self)
        
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Approximate pricing for Gemini 1.5 Flash (as of mid 2024)
        # Input: $0.35 per 1M tokens
        # Output: $1.05 per 1M tokens
        return (prompt_tokens * 0.00000035) + (completion_tokens * 0.00000105)
