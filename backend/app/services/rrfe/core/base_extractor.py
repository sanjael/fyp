from abc import ABC, abstractmethod
from typing import List, Any
from langchain_core.documents import Document

class BaseFeatureExtractor(ABC):
    @property
    @abstractmethod
    def feature_name(self) -> str:
        """Return the precise name of the feature in the schema."""
        pass
        
    @abstractmethod
    def extract(self, query: str, docs: List[Document]) -> float:
        """Extract the feature score from [0.0, 1.0]."""
        pass
        
    def validate(self, query: str, docs: List[Document]) -> bool:
        """Return True if extraction is possible (e.g. metadata exists)."""
        return True
