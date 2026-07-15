"""
Vector Store Module
Manages ChromaDB for persistent vector storage and semantic retrieval.
"""

import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import chromadb
from chromadb.config import Settings
import numpy as np

import config
from modules.embedding_engine import EmbeddingEngine
from modules.document_processor import DocumentChunk


class VectorStore:
    """
    ChromaDB-backed vector store for RAGShield.
    Handles document indexing, metadata storage, and semantic search.
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine()

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=config.VECTOR_DB_PATH,
        )

        # Main document collection
        self.collection = self.client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Use cosine distance
        )

        # Poisoned documents collection (Phase 2)
        self.poisoned_collection = self.client.get_or_create_collection(
            name=config.CHROMA_POISONED_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

        print(f"[VectorStore] Initialized. Documents: {self.collection.count()}")

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Add document chunks to the vector store.
        Generates embeddings and stores with full metadata.
        Returns number of chunks added.
        """
        if not chunks:
            return 0

        # Prepare data
        texts = [c.text for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [c.to_dict() for c in chunks]

        # Remove text from metadata (already in documents)
        for m in metadatas:
            m.pop("text", None)
            # ChromaDB requires all values to be strings/ints/floats/bools
            m = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                 for k, v in m.items()}

        metadatas_clean = []
        for m in metadatas:
            clean = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            metadatas_clean.append(clean)

        # Generate embeddings
        embeddings = self.embedding_engine.embed_documents(texts)
        embeddings_list = embeddings.tolist()

        # Check for existing IDs to avoid duplicates
        existing = set()
        try:
            existing_data = self.collection.get(ids=ids)
            existing = set(existing_data["ids"])
        except Exception:
            pass

        # Filter out existing chunks
        new_data = [
            (ids[i], texts[i], embeddings_list[i], metadatas_clean[i])
            for i in range(len(ids))
            if ids[i] not in existing
        ]

        if not new_data:
            print("[VectorStore] All chunks already indexed.")
            return 0

        new_ids, new_texts, new_embeddings, new_metadatas = zip(*new_data)

        # Add to ChromaDB
        self.collection.add(
            ids=list(new_ids),
            documents=list(new_texts),
            embeddings=list(new_embeddings),
            metadatas=list(new_metadatas),
        )

        print(f"[VectorStore] Added {len(new_ids)} chunks.")
        return len(new_ids)

    def search(
        self,
        query: str,
        top_k: int = None,
        source_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Semantic search: find top-K most relevant chunks for a query.

        Returns list of dicts with: text, score, metadata
        """
        top_k = top_k or config.TOP_K_RESULTS

        if self.collection.count() == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_engine.embed_query(query)

        # Build where filter
        where = None
        if source_filter:
            where = {"source": {"$eq": source_filter}}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, self.collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # Process results
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                # ChromaDB cosine distance → similarity: 1 - distance
                similarity_score = max(0.0, 1.0 - dist)

                chunks.append({
                    "chunk_id": results["ids"][0][i] if "ids" in results else f"chunk_{i}",
                    "text": doc,
                    "similarity_score": round(similarity_score, 4),
                    "source": meta.get("source", "unknown"),
                    "title": meta.get("title", ""),
                    "author": meta.get("author", "Unknown"),
                    "year": int(meta.get("year", 2024)),
                    "source_type": meta.get("source_type", "unknown"),
                    "page_number": int(meta.get("page_number", 1)),
                    "chunk_index": int(meta.get("chunk_index", i)),
                })

        return chunks

    def delete_document(self, source_filename: str) -> int:
        """Delete all chunks from a specific document."""
        try:
            results = self.collection.get(
                where={"source": {"$eq": source_filename}}
            )
            ids_to_delete = results["ids"]
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                print(f"[VectorStore] Deleted {len(ids_to_delete)} chunks for {source_filename}")
                return len(ids_to_delete)
        except Exception as e:
            print(f"[VectorStore] Delete error: {e}")
        return 0

    def list_documents(self) -> List[Dict]:
        """List all indexed documents with stats."""
        try:
            if self.collection.count() == 0:
                return []

            all_data = self.collection.get(include=["metadatas"])
            sources = {}
            for meta in all_data["metadatas"]:
                source = meta.get("source", "unknown")
                if source not in sources:
                    sources[source] = {
                        "filename": source,
                        "title": meta.get("title", source),
                        "author": meta.get("author", "Unknown"),
                        "year": meta.get("year", "Unknown"),
                        "source_type": meta.get("source_type", "unknown"),
                        "chunk_count": 0,
                    }
                sources[source]["chunk_count"] += 1

            return list(sources.values())
        except Exception as e:
            print(f"[VectorStore] List error: {e}")
            return []

    def get_total_chunks(self) -> int:
        """Return total number of indexed chunks."""
        return self.collection.count()

    def clear_all(self) -> bool:
        """Clear all documents from the vector store."""
        try:
            self.client.delete_collection(config.CHROMA_COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=config.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            return True
        except Exception as e:
            print(f"[VectorStore] Clear error: {e}")
            return False

    def add_poisoned_chunks(self, chunks: List[Dict]) -> int:
        """Add poisoned document chunks (Phase 2 — poisoning simulator)."""
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]

        embeddings = self.embedding_engine.embed_documents(texts)

        self.poisoned_collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=[{k: str(v) for k, v in c.items() if k != "text"} for c in chunks],
        )
        return len(chunks)
