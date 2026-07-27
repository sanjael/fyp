import os
from dotenv import load_dotenv

# Load .env from the backend root
load_dotenv()

class GlobalConfig:
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

    GENERATOR_LLM_MODEL = os.getenv("GENERATOR_LLM_MODEL", "qwen2.5:latest")

    EVALUATOR_PROVIDER = os.getenv("EVALUATOR_PROVIDER", "groq")
    EVALUATOR_LLM_MODEL = os.getenv("EVALUATOR_LLM_MODEL", "llama-3.3-70b-versatile")

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

global_config = GlobalConfig()