"""
Embedding Provider
==================
Owns ONLY the OllamaEmbeddings instance.

Deliberately contains NO chromadb import so that evaluation modules
(RAGAS, DeepEval) can import embeddings without triggering ChromaDB's
DefaultEmbeddingFunction / ONNXMiniLM_L6_V2 initialisation.
"""
from langchain_community.embeddings import OllamaEmbeddings
from app.core.config import global_config

_embeddings: OllamaEmbeddings | None = None


def get_embeddings() -> OllamaEmbeddings:
    """Return the singleton OllamaEmbeddings instance (lazy init)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OllamaEmbeddings(
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
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return get_embeddings().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return get_embeddings().embed_query(text)


embeddings = _LazyEmbeddings()
