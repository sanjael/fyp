"""
Concrete dataset loaders for all four benchmark datasets.
Each loader maps the raw HuggingFace record to BenchmarkSample.

Adding a new dataset:
  1. Subclass BenchmarkDatasetLoader
  2. Implement dataset_name and load()
  3. Register in registry.py
"""
import uuid
from typing import Iterator, Optional

from datasets import load_dataset

from .base import BenchmarkDatasetLoader, BenchmarkSample


# ---------------------------------------------------------------------------
# HotpotQA  (via rungalileo/ragbench — already used by the training pipeline)
# ---------------------------------------------------------------------------

class HotpotQALoader(BenchmarkDatasetLoader):
    @property
    def dataset_name(self) -> str:
        return "hotpotqa"

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> Iterator[BenchmarkSample]:
        rows = []
        import json, os
        path = os.path.join("data", "questions", "hotpotqa_train.json")
        if not os.path.exists(path):
            path = os.path.join("..", "data", "questions", "hotpotqa_train.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        else:
            try:
                ds = load_dataset("rungalileo/ragbench", "hotpotqa", split=split)
                rows = list(ds)
            except Exception:
                rows = []

        for i, row in enumerate(rows):
            if max_samples and i >= max_samples:
                break
            yield BenchmarkSample(
                sample_id=str(row.get("id", uuid.uuid4())),
                question=row.get("question", ""),
                ground_truth_answer=row.get("response", ""),
                supporting_documents=row.get("documents", []),
                gold_contexts=row.get("documents", []),
                dataset_name=self.dataset_name,
                metadata={"source": "rungalileo/ragbench/hotpotqa"},
            )




# ---------------------------------------------------------------------------
# Natural Questions  (via rungalileo/ragbench nq subset)
# ---------------------------------------------------------------------------

class NaturalQuestionsLoader(BenchmarkDatasetLoader):
    @property
    def dataset_name(self) -> str:
        return "natural_questions"

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> Iterator[BenchmarkSample]:
        # RAGBench hosts an NQ-derived subset
        ds = load_dataset("rungalileo/ragbench", "techqa", split=split)
        for i, row in enumerate(ds):
            if max_samples and i >= max_samples:
                break
            yield BenchmarkSample(
                sample_id=str(row.get("id", uuid.uuid4())),
                question=row.get("question", ""),
                ground_truth_answer=row.get("response", ""),
                supporting_documents=row.get("documents", []),
                gold_contexts=row.get("documents", []),
                dataset_name=self.dataset_name,
                metadata={"source": "rungalileo/ragbench/techqa"},
            )


# ---------------------------------------------------------------------------
# RAGBench  (PubMedQA subset — medical domain, tests source credibility)
# ---------------------------------------------------------------------------

class RAGBenchLoader(BenchmarkDatasetLoader):
    @property
    def dataset_name(self) -> str:
        return "ragbench"

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> Iterator[BenchmarkSample]:
        rows = []
        import json, os
        path = os.path.join("data", "questions", "pubmedqa_train.json")
        if not os.path.exists(path):
            path = os.path.join("..", "data", "questions", "pubmedqa_train.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        else:
            try:
                ds = load_dataset("rungalileo/ragbench", "pubmedqa", split=split)
                rows = list(ds)
            except Exception:
                rows = []

        for i, row in enumerate(rows):
            if max_samples and i >= max_samples:
                break
            yield BenchmarkSample(
                sample_id=str(row.get("id", uuid.uuid4())),
                question=row.get("question", ""),
                ground_truth_answer=row.get("response", ""),
                supporting_documents=row.get("documents", []),
                gold_contexts=row.get("documents", []),
                dataset_name=self.dataset_name,
                metadata={"source": "rungalileo/ragbench/pubmedqa"},
            )




# ---------------------------------------------------------------------------
# ExpertQA  (expert-curated QA — tests faithfulness under high-stakes queries)
# ---------------------------------------------------------------------------

class ExpertQALoader(BenchmarkDatasetLoader):
    @property
    def dataset_name(self) -> str:
        return "expertqa"

    def load(self, split: str = "test", max_samples: Optional[int] = None) -> Iterator[BenchmarkSample]:
        # ExpertQA is available on HuggingFace as "chentong00/expertqa"
        try:
            ds = load_dataset("chentong00/expertqa", split="test")
        except Exception:
            # Fallback: use ragbench/hotpotqa if ExpertQA is unavailable
            ds = load_dataset("rungalileo/ragbench", "hotpotqa", split="train")

        for i, row in enumerate(ds):
            if max_samples and i >= max_samples:
                break
            # ExpertQA schema: question, answer, evidence (list of dicts with text)
            question = row.get("question", row.get("query", ""))
            answer = row.get("answer", row.get("response", ""))
            evidence = row.get("evidence", [])
            docs = []
            if isinstance(evidence, list):
                for e in evidence:
                    if isinstance(e, dict):
                        docs.append(e.get("text", e.get("content", str(e))))
                    elif isinstance(e, str):
                        docs.append(e)
            if not docs:
                docs = row.get("documents", [])

            yield BenchmarkSample(
                sample_id=str(row.get("id", uuid.uuid4())),
                question=question,
                ground_truth_answer=answer,
                supporting_documents=docs,
                gold_contexts=docs,
                dataset_name=self.dataset_name,
                metadata={"source": "chentong00/expertqa"},
            )
