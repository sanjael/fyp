import os
from dotenv import load_dotenv

# Load .env from the backend root
load_dotenv()

class GlobalConfig:
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
    USE_CHROMA_HTTP = os.getenv("USE_CHROMA_HTTP", "false").lower() in ("true", "1", "yes")
    ENABLE_CHROMA_TELEMETRY = os.getenv("ENABLE_CHROMA_TELEMETRY", "false").lower() in ("true", "1", "yes")

    GENERATOR_LLM_MODEL = os.getenv("GENERATOR_LLM_MODEL", "qwen2.5:latest")

    EVALUATOR_PROVIDER = os.getenv("EVALUATOR_PROVIDER", "groq")
    EVALUATOR_LLM_MODEL = os.getenv("EVALUATOR_LLM_MODEL", "llama-3.3-70b-versatile")
    EVALUATOR_CONCURRENCY = int(os.getenv("EVALUATOR_CONCURRENCY", "1"))
    EVALUATOR_MAX_RETRIES = int(os.getenv("EVALUATOR_MAX_RETRIES", "3"))
    EVALUATOR_MAX_WAIT = float(os.getenv("EVALUATOR_MAX_WAIT", "30.0"))
    EVALUATOR_TIMEOUT = float(os.getenv("EVALUATOR_TIMEOUT", "300.0"))


    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


# Disable ChromaDB internal telemetry natively via environment variable when telemetry is disabled
if not os.getenv("ENABLE_CHROMA_TELEMETRY", "false").lower() in ("true", "1", "yes"):
    os.environ["ANONYMIZED_TELEMETRY"] = "False"

global_config = GlobalConfig()