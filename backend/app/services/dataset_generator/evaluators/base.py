from abc import ABC, abstractmethod
from typing import List, Optional
from langchain_core.documents import Document

class BaseEvaluator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the evaluator's metric."""
        pass
        
    @abstractmethod
    def evaluate(self, query: str, docs: List[Document]) -> Optional[float]:
        """
        Evaluate the retrieval context.
        Must return a float between 0.0 and 1.0, or None if it fails.
        """
        pass
