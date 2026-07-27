"""
Base interface for all benchmark dataset loaders.
To add a new dataset: subclass BenchmarkDatasetLoader and register it in registry.py.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, List, Optional


@dataclass
class BenchmarkSample:
    """Canonical sample format shared across all benchmark datasets."""
    sample_id: str
    question: str
    ground_truth_answer: str
    # Raw supporting documents (strings) provided by the dataset
    supporting_documents: List[str] = field(default_factory=list)
    # Optional gold context passages (for recall computation)
    gold_contexts: List[str] = field(default_factory=list)
    dataset_name: str = ""
    metadata: dict = field(default_factory=dict)


class BenchmarkDatasetLoader(ABC):
    """Abstract loader — one subclass per benchmark dataset."""

    @property
    @abstractmethod
    def dataset_name(self) -> str: ...

    @abstractmethod
    def load(self, split: str = "test", max_samples: Optional[int] = None) -> Iterator[BenchmarkSample]: ...
