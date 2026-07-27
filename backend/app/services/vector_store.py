"""
Vector Store Service
====================
Owns ALL ChromaDB logic.

This module is the ONLY place in the codebase that imports chromadb.
Evaluation modules (RAGAS, DeepEval, RRFE) must never import this file.

ChromaDB is initialised lazily — the client is created only when the
first vector-store operation is requested, not at import time.
"""
import logging
import os
from typing import Any, List, Tuple
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from app.core.config import global_config
from app.services.embedding_provider import get_embeddings

__all__ = [
    "get_chroma_client",
    "_get_chroma_client",
    "get_vector_store",
    "add_documents_to_chroma",
    "search_documents",
    "delete_collection",
]

logger = logging.getLogger("app.services.vector_store")
_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Return the singleton ChromaDB client (lazy init, HTTP -> PersistentClient fallback)."""
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
            logger.warning(f"ChromaDB HTTP unavailable ({e}). Falling back to PersistentClient.")
            _chroma_client = chromadb.PersistentClient(
                path=os.path.join(os.path.dirname(__file__), "..", "..", "chroma")
            )
    return _chroma_client


# Private alias for backward compatibility with older imports
_get_chroma_client = get_chroma_client


def get_vector_store(collection_name: str = "ragguard_docs") -> Chroma:
    """Return a LangChain Chroma vector store instance bound to the specified collection."""
    return Chroma(
        client=get_chroma_client(),
        collection_name=collection_name,
        embedding_function=get_embeddings(),
    )


def add_documents_to_chroma(chunks: List[Document], collection_name: str = "ragguard_docs") -> List[str]:
    """Add document chunks to the Chroma vector store."""
    return get_vector_store(collection_name).add_documents(chunks)


def search_documents(
    query: str, k: int = 5, collection_name: str = "ragguard_docs"
) -> List[Tuple[Document, float]]:
    """Search for relevant documents with similarity scores."""
    return get_vector_store(collection_name).similarity_search_with_score(query, k=k)


def delete_collection(collection_name: str = "ragguard_docs") -> None:
    """Delete a ChromaDB collection if it exists."""
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
    except Exception as e:
        logger.warning(f"Could not delete collection {collection_name}: {e}")

