from typing import Iterator, Dict, Any
from .base import BaseDatasetLoader

class HuggingFaceLoader(BaseDatasetLoader):
    def load_split(self, dataset_name: str, split_name: str, streaming: bool = False) -> Iterator[Dict[str, Any]]:
        """
        Loads a HuggingFace dataset. We use a lazy import to avoid unnecessary overhead 
        if the library isn't installed during simple test runs.
        """
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("Please install datasets (`pip install datasets`) to use HuggingFaceLoader.")
            
        # We map dataset_name 'hotpotqa' to the rungalileo/ragbench subset
        if dataset_name in ["hotpotqa", "pubmedqa", "techqa"]:
            dataset = load_dataset("rungalileo/ragbench", dataset_name, split=split_name, streaming=streaming)
        else:
            dataset = load_dataset(dataset_name, split=split_name, streaming=streaming)
        
        for record in dataset:
            yield record
