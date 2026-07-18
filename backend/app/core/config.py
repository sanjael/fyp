import os

class GlobalConfig:
    # Service Endpoints
    # We default to localhost if not specified, making it easy to run locally
    # In Docker, these will be overridden via environment variables.
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
    
    # LLM Configurations
    # Explicitly configure the models used across the pipeline
    GENERATOR_LLM_MODEL = os.getenv("GENERATOR_LLM_MODEL", "qwen2.5:latest")
    
    # Evaluator Configurations
    EVALUATOR_PROVIDER = os.getenv("EVALUATOR_PROVIDER", "groq") # 'ollama', 'google', or 'groq'
    EVALUATOR_LLM_MODEL = os.getenv("EVALUATOR_LLM_MODEL", "llama-3.3-70b-versatile") 
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

global_config = GlobalConfig()
