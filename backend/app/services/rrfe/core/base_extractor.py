from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document
from ..models import FeatureResult


class BaseFeatureExtractor(ABC):
    """Contract for all RRFE feature extractors.

    Every extractor must return a FeatureResult containing:
      score            – Optional[float] in [0, 1], or None when data is unavailable
      confidence       – float [0, 1]  (how certain we are about the score)
      reason           – human-readable explanation
      evidence_source  – where the data came from, or "Unavailable" when missing

    Rule: score=None MUST be returned (with confidence=0) whenever the feature
    cannot be computed due to missing or unavailable input data.
    score=0.5 must NEVER be used as a neutral fallback for missing data.
    """

    @property
    @abstractmethod
    def feature_name(self) -> str:
        """Unique snake_case name used as the dict key in the feature vector."""
        ...

    @abstractmethod
    def extract(self, query: str, docs: List[Document]) -> FeatureResult:
        """Extract the feature and return a fully-explained FeatureResult."""
        ...

    def validate(self, query: str, docs: List[Document]) -> bool:
        """Return True if extraction can proceed (e.g. required metadata exists)."""
        return True
