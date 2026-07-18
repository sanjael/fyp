import hashlib
from typing import List
from langchain_core.documents import Document

from ....services.embedding_engine import search_documents, add_documents_to_chroma
from ....services.document_processor import chunk_document

class RAGProcessor:
    def __init__(self):
        # We maintain a persistent set of hashes to avoid re-indexing
        self.indexed_hashes = set()
        
    def _hash_doc(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def index_documents(self, documents: List[str]):
        """
        Chunks and embeds documents into the persistent ChromaDB, 
        skipping any that are already indexed.
        """
        new_docs = []
        for text in documents:
            h = self._hash_doc(text)
            if h not in self.indexed_hashes:
                new_docs.append(text)
                self.indexed_hashes.add(h)
                
        if new_docs:
            chunks = []
            for doc_text in new_docs:
                # We use a dummy filename just to satisfy metadata requirements in chunking
                chunks.extend(chunk_document(doc_text, filename="dataset_document.txt"))
            
            if chunks:
                try:
                    add_documents_to_chroma(chunks)
                except Exception as e:
                    print(f"Failed to add documents to ChromaDB: {e}")

    def retrieve(self, query: str, top_k: int = 3) -> List[Document]:
        """
        Retrieves top K chunks using the existing embedding engine.
        """
        try:
            results = search_documents(query, k=top_k)
            # results is a list of (Document, score) tuples
            return [doc for doc, score in results]
        except Exception as e:
            print(f"Retrieval failed: {e}")
            # Explicit fallback if vector DB is down
            return []
