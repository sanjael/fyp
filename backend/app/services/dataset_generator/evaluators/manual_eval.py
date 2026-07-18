from typing import List, Optional
from langchain_core.documents import Document
from .base import BaseEvaluator

class ManualExpertEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "manual_expert_score"

    def evaluate(self, query: str, docs: List[Document]) -> Optional[float]:
        # Returns None by default since manual annotations are done async post-generation
        return None
