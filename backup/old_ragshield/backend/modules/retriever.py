"""
Retriever Module
Semantic retrieval of relevant document chunks from the vector store.
"""

from typing import List, Dict, Optional

import config
from modules.vector_store import VectorStore


class Retriever:
    """
    Retrieves semantically relevant document chunks for a given query.
    This is the standard RAG retrieval step before Context Shield processing.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        source_filter: Optional[str] = None,
        min_similarity: float = None,
    ) -> List[Dict]:
        """
        Retrieve top-K relevant chunks for a query.

        Args:
            query: User's question
            top_k: Number of results to fetch (default from config)
            source_filter: Limit search to specific document
            min_similarity: Minimum similarity threshold

        Returns:
            List of chunk dicts with similarity scores
        """
        top_k = top_k or config.TOP_K_RESULTS
        min_similarity = min_similarity or config.SIMILARITY_THRESHOLD

        print(f"[Retriever] Query: '{query[:80]}...' | top_k={top_k}")

        # Fetch from vector store
        raw_results = self.vector_store.search(
            query=query,
            top_k=top_k,
            source_filter=source_filter,
        )

        # Apply minimum similarity filter
        filtered = [
            chunk for chunk in raw_results
            if chunk["similarity_score"] >= min_similarity
        ]

        print(f"[Retriever] Retrieved {len(raw_results)} -> filtered to {len(filtered)} chunks")

        # Sort by similarity (descending)
        filtered.sort(key=lambda x: x["similarity_score"], reverse=True)

        return filtered

    def retrieve_with_metadata(self, query: str, top_k: int = None) -> Dict:
        """
        Retrieve chunks and return with full retrieval metadata for explainability.
        """
        top_k = top_k or config.TOP_K_RESULTS
        all_results = self.vector_store.search(query=query, top_k=top_k)

        above_threshold = [
            c for c in all_results
            if c["similarity_score"] >= config.SIMILARITY_THRESHOLD
        ]
        below_threshold = [
            c for c in all_results
            if c["similarity_score"] < config.SIMILARITY_THRESHOLD
        ]

        return {
            "query": query,
            "total_retrieved": len(all_results),
            "above_threshold": len(above_threshold),
            "below_threshold": len(below_threshold),
            "threshold_used": config.SIMILARITY_THRESHOLD,
            "chunks": above_threshold,
            "rejected_chunks": below_threshold,
        }
