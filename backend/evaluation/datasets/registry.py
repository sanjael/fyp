"""
Dataset registry.
To add a new dataset: import its loader and add it to REGISTRY.
"""
from .loaders import (
    HotpotQALoader,
    NaturalQuestionsLoader,
    RAGBenchLoader,
    ExpertQALoader,
)
from .base import BenchmarkDatasetLoader
from typing import Dict

REGISTRY: Dict[str, BenchmarkDatasetLoader] = {
    "hotpotqa":         HotpotQALoader(),
    "pubmedqa":         RAGBenchLoader(),
    "natural_questions": NaturalQuestionsLoader(),
    "ragbench":         RAGBenchLoader(),
    "expertqa":         ExpertQALoader(),
}



def get_loader(name: str) -> BenchmarkDatasetLoader:
    if name not in REGISTRY:
        raise ValueError(f"Unknown dataset '{name}'. Available: {list(REGISTRY.keys())}")
    return REGISTRY[name]
