"""
RAGShield Configuration Module
Manages all environment variables and app settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ─── Base Paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "vector_db"))
PDF_UPLOAD_PATH = os.getenv("PDF_UPLOAD_PATH", str(BASE_DIR / "data" / "pdfs"))
POISONED_DATA_PATH = os.getenv("POISONED_DATA_PATH", str(BASE_DIR / "data" / "poisoned"))
EVALUATION_DATA_PATH = str(BASE_DIR / "data" / "evaluation")

# Create directories if not exist
for path in [VECTOR_DB_PATH, PDF_UPLOAD_PATH, POISONED_DATA_PATH, EVALUATION_DATA_PATH]:
    Path(path).mkdir(parents=True, exist_ok=True)

# ─── App Settings ─────────────────────────────────────────────────────────────
APP_NAME = os.getenv("APP_NAME", "RAGShield")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ─── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── Embedding Model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# ─── LLM Settings ─────────────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# ─── Retrieval Settings ───────────────────────────────────────────────────────
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "10"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))
MAX_CONTEXT_CHUNKS = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))

# ─── Context Shield Thresholds ────────────────────────────────────────────────
DUPLICATE_THRESHOLD = float(os.getenv("DUPLICATE_THRESHOLD", "0.95"))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.65"))
CONTRADICTION_THRESHOLD = float(os.getenv("CONTRADICTION_THRESHOLD", "0.3"))
FRESHNESS_PENALTY_YEARS = int(os.getenv("FRESHNESS_PENALTY_YEARS", "5"))

# ─── CQS Weights ──────────────────────────────────────────────────────────────
CQS_WEIGHT_RELEVANCE = float(os.getenv("CQS_WEIGHT_RELEVANCE", "0.4"))
CQS_WEIGHT_CREDIBILITY = float(os.getenv("CQS_WEIGHT_CREDIBILITY", "0.3"))
CQS_WEIGHT_CONSISTENCY = float(os.getenv("CQS_WEIGHT_CONSISTENCY", "0.2"))
CQS_WEIGHT_FRESHNESS = float(os.getenv("CQS_WEIGHT_FRESHNESS", "0.1"))

# ─── Risk Engine Thresholds ───────────────────────────────────────────────────
RISK_LOW_THRESHOLD = int(os.getenv("RISK_LOW_THRESHOLD", "30"))
RISK_HIGH_THRESHOLD = int(os.getenv("RISK_HIGH_THRESHOLD", "60"))

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_STR.split(",")]

# ─── Source Reliability Scores ────────────────────────────────────────────────
SOURCE_RELIABILITY_SCORES = {
    "research_paper": 95,
    "arxiv": 93,
    "textbook": 90,
    "government": 88,
    "wikipedia": 72,
    "news": 60,
    "blog": 40,
    "unknown": 50,
}

# ─── ChromaDB Collection Name ─────────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "ragshield_docs"
CHROMA_POISONED_COLLECTION = "ragshield_poisoned"

# ─── Chunking Settings ────────────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# ─── Validation ───────────────────────────────────────────────────────────────
if not GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY is not set. LLM generation will fail.")
