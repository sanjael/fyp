from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any

class BaseDatasetLoader(ABC):
    @abstractmethod
    def load_split(self, dataset_name: str, split_name: str, streaming: bool = True) -> Iterator[Dict[str, Any]]:
        """
        Yields raw records from the specified dataset split.
        """
        pass
