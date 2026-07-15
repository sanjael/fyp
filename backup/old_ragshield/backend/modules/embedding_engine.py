"""
Embedding Engine Module
Generates vector embeddings using BAAI/bge-small-en-v1.5 for semantic search.
"""

import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

import config


class EmbeddingEngine:
    """
    Generates dense vector embeddings using a pre-trained sentence transformer.
    Uses BAAI/bge-small-en-v1.5 — optimal balance of speed and accuracy for RAG.
    """

    _instance = None  # Singleton to avoid re-loading the model

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        print(f"[EmbeddingEngine] Loading model: {config.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self._initialized = True
        print(f"[EmbeddingEngine] Model loaded. Embedding dim: {self.embedding_dim}")

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of strings to embed
            batch_size: Number of texts per batch
            normalize: If True, L2-normalize embeddings (required for cosine similarity)
            show_progress: Show progress bar for large batches

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        # BGE models benefit from a query instruction prefix
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.
        BGE models use a specific instruction prefix for queries.
        """
        # BGE instruction for retrieval queries
        instruction = "Represent this sentence for searching relevant passages: "
        query_with_instruction = instruction + query

        embedding = self.model.encode(
            [query_with_instruction],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding[0]

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for document chunks (no instruction prefix).
        """
        return self.embed_texts(texts, show_progress=len(texts) > 50)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two normalized vectors."""
        # If already normalized, this is just dot product
        return float(np.dot(vec1, vec2))

    def batch_cosine_similarity(
        self, query_vec: np.ndarray, doc_vecs: np.ndarray
    ) -> np.ndarray:
        """Compute cosine similarity between a query and multiple documents."""
        return np.dot(doc_vecs, query_vec)

    def get_embedding_dim(self) -> int:
        """Return the embedding dimension."""
        return self.embedding_dim
