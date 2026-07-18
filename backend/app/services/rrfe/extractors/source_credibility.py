from typing import List
from langchain_core.documents import Document
from ..core.base_extractor import BaseFeatureExtractor
from ..config import config

class SourceCredibilityExtractor(BaseFeatureExtractor):
    @property
    def feature_name(self) -> str:
        return "source_credibility"

    def validate(self, query: str, docs: List[Document]) -> bool:
        return any(doc.metadata.get("estimated_credibility") is not None for doc in docs)

    def extract(self, query: str, docs: List[Document]) -> float:
        if not docs:
            return config.DEFAULT_CREDIBILITY_SCORE
            
        scores = []
        for doc in docs:
            credibility = doc.metadata.get("estimated_credibility")
            if credibility is not None:
                try:
                    scores.append(float(credibility))
                except ValueError:
                    scores.append(config.DEFAULT_CREDIBILITY_SCORE)
            else:
                scores.append(config.DEFAULT_CREDIBILITY_SCORE)
                
        return sum(scores) / len(scores)
