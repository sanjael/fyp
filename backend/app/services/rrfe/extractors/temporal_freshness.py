from typing import List
from datetime import datetime
from langchain_core.documents import Document
from ..core.base_extractor import BaseFeatureExtractor
from ..config import config

class TemporalFreshnessExtractor(BaseFeatureExtractor):
    @property
    def feature_name(self) -> str:
        return "temporal_freshness"

    def validate(self, query: str, docs: List[Document]) -> bool:
        # Check if at least one doc has a date
        return any(doc.metadata.get("document_date") or doc.metadata.get("ingestion_date") for doc in docs)

    def extract(self, query: str, docs: List[Document]) -> float:
        if not docs:
            return config.DEFAULT_TEMPORAL_SCORE
            
        freshness_scores = []
        now = datetime.now()
        
        for doc in docs:
            date_str = doc.metadata.get("document_date") or doc.metadata.get("ingestion_date")
            if not date_str:
                freshness_scores.append(config.DEFAULT_TEMPORAL_SCORE)
                continue
                
            try:
                # Basic ISO parse
                doc_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                age_days = (now.astimezone() - doc_date.astimezone()).days
                
                # Heuristic: Score drops to 0.5 at 180 days, 0.1 at 3 years
                score = max(0.0, 1.0 - (age_days / 1000.0))
                freshness_scores.append(score)
            except Exception:
                freshness_scores.append(config.DEFAULT_TEMPORAL_SCORE)
                
        return sum(freshness_scores) / len(freshness_scores)
