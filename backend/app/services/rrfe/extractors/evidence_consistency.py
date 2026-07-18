import numpy as np
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.documents import Document
from ..core.base_extractor import BaseFeatureExtractor
from ..config import config
from ...embedding_engine import embeddings

class EvidenceConsistencyExtractor(BaseFeatureExtractor):
    @property
    def feature_name(self) -> str:
        return "evidence_consistency"

    def extract(self, query: str, docs: List[Document]) -> float:
        if not docs or len(docs) < 2:
            return config.DEFAULT_CONSISTENCY_SCORE
            
        try:
            texts = [doc.page_content for doc in docs]
            vectors = embeddings.embed_documents(texts)
            
            # Calculate pairwise cosine similarity
            sim_matrix = cosine_similarity(vectors)
            
            # Extract upper triangle excluding diagonal
            upper_tri_indices = np.triu_indices_from(sim_matrix, k=1)
            pairwise_sims = sim_matrix[upper_tri_indices]
            
            if len(pairwise_sims) == 0:
                return config.DEFAULT_CONSISTENCY_SCORE
                
            # Average similarity as a proxy for consistency
            avg_sim = float(np.mean(pairwise_sims))
            
            # Normalize to [0,1] just in case
            return max(0.0, min(1.0, avg_sim))
            
        except Exception as e:
            print(f"Error in EvidenceConsistencyExtractor: {e}")
            return config.DEFAULT_CONSISTENCY_SCORE
