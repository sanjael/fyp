from abc import ABC, abstractmethod
from typing import List
from ..models import DatasetSample

class BaseExporter(ABC):
    @abstractmethod
    def export(self, samples: List[DatasetSample], filepath: str) -> bool:
        """Export samples to the given filepath. Returns True if successful."""
        pass
