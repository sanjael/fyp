from ...core.config import global_config
from .base import EvaluatorProvider

_provider_instance = None

def get_evaluator_provider() -> EvaluatorProvider:
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance
        
    provider_name = global_config.EVALUATOR_PROVIDER.lower()
    model_name = global_config.EVALUATOR_LLM_MODEL
    
    if provider_name == "google":
        from .gemini import GeminiProvider
        _provider_instance = GeminiProvider(model_name=model_name)
    elif provider_name == "ollama":
        from .ollama import OllamaProvider
        _provider_instance = OllamaProvider(model_name=model_name)
    elif provider_name == "groq":
        from .groq import GroqProvider
        _provider_instance = GroqProvider(model_name=model_name)
    else:
        raise ValueError(f"Unknown evaluator provider: {provider_name}")
        
    return _provider_instance
