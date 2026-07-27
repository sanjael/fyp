"""
Vector Store
============
Owns ALL ChromaDB logic.

This module is the ONLY place in the codebase that imports chromadb.
Evaluation modules (RAGAS, DeepEval, RRFE) must never import this file.

ChromaDB is initialised lazily — the client is created only when the
first vector-store operation is requested, not at import time.
"""
import os
import chromadb
from langchain_community.vectorstores import Chroma

from app.core.config import global_config
from app.services.embedding_provider import get_embeddings

_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Return the singleton ChromaDB client (lazy init, HTTP → PersistentClient fallback)."""
    global _chroma_client
    if _chroma_client is None:
        try:
            client = chromadb.HttpClient(
                host=global_config.CHROMA_HOST,
                port=global_config.CHROMA_PORT,
            )
            client.heartbeat()
            _chroma_client = client
        except Exception as e:
            print(f"ChromaDB HTTP unavailable ({e}). Falling back to PersistentClient.")
            _chroma_client = chromadb.PersistentClient(
                path=os.path.join(os.path.dirname(__file__), "..", "..", "chroma")
            )
    return _chroma_client


# Keep the private alias so existing runner code that imported
# `_get_chroma_client` from embedding_engine still works via the shim.
_get_chroma_client = get_chroma_client


def get_vector_store(collection_name: str = "ragguard_docs") -> Chroma:
    return Chroma(
        client=get_chroma_client(),
        collection_name=collection_name,
        embedding_function=get_embeddings(),
    )


def add_documents_to_chroma(chunks, collection_name: str = "ragguard_docs"):
    return get_vector_store(collection_name).add_documents(chunks)


def search_documents(query: str, k: int = 5, collection_name: str = "ragguard_docs"):
    return get_vector_store(collection_name).similarity_search_with_score(query, k=k)
