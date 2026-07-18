from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models import UnifiedDocumentSchema

class BaseAdapter(ABC):
    @abstractmethod
    def extract(self, raw_record: Dict[str, Any]) -> UnifiedDocumentSchema:
        """
        Transforms a dataset-specific raw record into the UnifiedDocumentSchema.
        """
        pass
