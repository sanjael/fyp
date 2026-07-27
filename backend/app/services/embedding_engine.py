"""
embedding_engine — backward-compatibility shim
===============================================
All logic has been split into:
  - app.services.embedding_provider  (OllamaEmbeddings, no chromadb)
  - app.services.vector_store        (ChromaDB, lazy)

New code should import directly from those modules.
This shim exists only so that any remaining `from app.services.embedding_engine import …`
calls continue to work without modification.
"""
from app.services.embedding_provider import get_embeddings, embeddings
from app.services.vector_store import (
    get_chroma_client as _get_chroma_client,
    get_vector_store,
    add_documents_to_chroma,
    search_documents,
    delete_collection,
)

__all__ = [
    "get_embeddings",
    "embeddings",
    "_get_chroma_client",
    "get_vector_store",
    "add_documents_to_chroma",
    "search_documents",
    "delete_collection",
]

