"""
Embedding Provider Service
==========================
Owns ONLY the OllamaEmbeddings instance.

Deliberately contains NO chromadb import so that evaluation modules
(RAGAS, DeepEval) can import embeddings without triggering ChromaDB's
DefaultEmbeddingFunction / ONNXMiniLM_L6_V2 initialisation.
"""
from typing import List
import requests
from langchain_community.embeddings import OllamaEmbeddings
from app.core.config import global_config

__all__ = ["get_embeddings", "embeddings"]

class BatchedOllamaEmbeddings(OllamaEmbeddings):
    """
    Performance-optimized OllamaEmbeddings subclass.
    Uses Ollama's native /api/embed REST endpoint to send texts in parallel HTTP
    batches rather than standard OllamaEmbeddings' 1-by-1 sequential HTTP POSTs.
    """
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = self.base_url.rstrip("/") + "/api/embed"
        all_embeddings: List[List[float]] = []
        batch_size = 64
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            resp = requests.post(url, json={"model": self.model, "input": chunk})
            resp.raise_for_status()
            data = resp.json()
            all_embeddings.extend(data.get("embeddings", []))
        return all_embeddings


_embeddings: OllamaEmbeddings | None = None


def get_embeddings() -> OllamaEmbeddings:
    """Return the singleton OllamaEmbeddings instance (lazy init)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = BatchedOllamaEmbeddings(
            base_url=global_config.OLLAMA_HOST,
            model=global_config.EMBEDDING_MODEL,
        )
    return _embeddings


class _LazyEmbeddings:
    """
    Module-level proxy so RRFE extractors can do:
        from app.services.embedding_provider import embeddings
    without triggering initialisation at import time.
    """
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return get_embeddings().embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return get_embeddings().embed_query(text)


embeddings = _LazyEmbeddings()

