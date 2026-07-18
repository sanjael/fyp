import numpy as np
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.documents import Document
from ..core.base_extractor import BaseFeatureExtractor
from ..config import config
from ...embedding_engine import embeddings

class EvidenceSufficiencyExtractor(BaseFeatureExtractor):
    @property
    def feature_name(self) -> str:
        return "evidence_sufficiency"

    def extract(self, query: str, docs: List[Document]) -> float:
        if not docs or not query:
            return config.DEFAULT_SUFFICIENCY_SCORE
            
        try:
            query_vector = np.array(embeddings.embed_query(query)).reshape(1, -1)
            
            texts = [doc.page_content for doc in docs]
            doc_vectors = np.array(embeddings.embed_documents(texts))
            
            # Calculate similarity of each doc to the query
            sims = cosine_similarity(query_vector, doc_vectors)[0]
            
            # Max similarity as a proxy for sufficiency (if one doc covers it well, it's sufficient)
            max_sim = float(np.max(sims))
            
            # Normalize to [0,1]
            return max(0.0, min(1.0, max_sim))
            
        except Exception as e:
            print(f"Error in EvidenceSufficiencyExtractor: {e}")
            return config.DEFAULT_SUFFICIENCY_SCORE
