"""
RAGAS evaluation wrapper — ragas 0.1.x API
===========================================
Computes:
  - faithfulness
  - answer_relevancy
  - context_precision
  - context_recall
  - context_entity_recall  (when available)

LLM provider:  configured via EVALUATOR_PROVIDER env var (groq / google / ollama)
Embeddings:    OllamaEmbeddings via embedding_provider (zero chromadb dependency)

ragas 0.1.x API notes
---------------------
  evaluate(dataset, metrics, llm, embeddings)
    llm        — must be ragas.llms.LangchainLLMWrapper(langchain_model)
    embeddings — must be a langchain BaseEmbeddings instance
                 (ragas wraps it internally with LangchainEmbeddingsWrapper)
"""
import logging
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger("eval.ragas")

RAGAS_AVAILABLE = False
_ENTITY_RECALL = False

try:
    from datasets import Dataset, Features, Value, Sequence
    from ragas import evaluate
    from ragas.metrics import (
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    )
    try:
        from ragas.metrics import context_entity_recall
        _ENTITY_RECALL = True
    except ImportError:
        pass

    # ragas 0.1.x uses LangchainLLMWrapper — NOT our custom ProviderLangchainWrapper.
    # ProviderLangchainWrapper is a BaseChatModel subclass designed for DeepEval/direct
    # LangChain use. Passing it to ragas works but bypasses ragas's own retry/run_config
    # logic. Using LangchainLLMWrapper is the correct ragas 0.1.x integration point.
    from ragas.llms import LangchainLLMWrapper

    from app.core.evaluator_provider.factory import get_evaluator_provider
    # Import from embedding_provider — deliberately NO chromadb import in this path.
    from app.services.embedding_provider import get_embeddings

    RAGAS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAGAS not available: {e}")

from ..runners.result import PipelineResult
from .result import MetricResult


class RagasEvaluator:
    def __init__(self):
        if not RAGAS_AVAILABLE:
            return
        provider = get_evaluator_provider()
        # get_langchain_model() returns the raw LangChain model (ChatGroq, ChatOllama, etc.)
        # Wrap it with ragas's own LangchainLLMWrapper so ragas controls retry/run_config.
        self._llm = LangchainLLMWrapper(provider.get_langchain_model())
        # get_embeddings() returns OllamaEmbeddings — a standard LangChain BaseEmbeddings.
        # ragas 0.1.x wraps it internally with LangchainEmbeddingsWrapper.
        self._embeddings = get_embeddings()
        self._metrics = [context_precision, context_recall, faithfulness, answer_relevancy]
        if _ENTITY_RECALL:
            self._metrics.append(context_entity_recall)

    def evaluate(self, result: PipelineResult) -> MetricResult:
        metric_result = MetricResult(sample_id=result.sample_id, pipeline=result.pipeline)

        if not RAGAS_AVAILABLE:
            metric_result.error = "ragas not installed"
            return metric_result

        if not result.retrieved_contexts or not result.generated_answer:
            metric_result.error = "empty contexts or answer"
            return metric_result

        try:
            dataset = Dataset.from_dict(
                {
                    "question":    [result.question],
                    "contexts":    [result.retrieved_contexts],
                    "answer":      [result.generated_answer],
                    "ground_truth": [result.ground_truth_answer],
                },
                features=Features({
                    "question":     Value("string"),
                    "contexts":     Sequence(Value("string")),
                    "answer":       Value("string"),
                    "ground_truth": Value("string"),
                }),
            )
            scores = evaluate(
                dataset,
                metrics=self._metrics,
                llm=self._llm,
                embeddings=self._embeddings,
            )
            metric_result.scores = {
                "ragas_faithfulness":      _safe_float(scores.get("faithfulness")),
                "ragas_answer_relevancy":  _safe_float(scores.get("answer_relevancy")),
                "ragas_context_precision": _safe_float(scores.get("context_precision")),
                "ragas_context_recall":    _safe_float(scores.get("context_recall")),
            }
            if _ENTITY_RECALL:
                metric_result.scores["ragas_context_entity_recall"] = _safe_float(
                    scores.get("context_entity_recall")
                )
        except Exception as e:
            metric_result.error = str(e)
            logger.error(f"RAGAS evaluation failed for {result.sample_id}: {e}")

        return metric_result


def _safe_float(val) -> Optional[float]:
    try:
        import math
        v = float(val)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None
