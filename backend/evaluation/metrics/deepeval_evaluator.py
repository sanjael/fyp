"""
DeepEval evaluation wrapper for the benchmark pipeline.

Computes:
  - faithfulness
  - answer_relevancy
  - hallucination
  - contextual_precision
  - contextual_recall
  - bias          (optional — skipped if unavailable)
  - toxicity      (optional — skipped if unavailable)
"""
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger("eval.deepeval")

try:
    from deepeval.metrics import (
        FaithfulnessMetric,
        AnswerRelevancyMetric,
        HallucinationMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
    )
    try:
        from deepeval.metrics import BiasMetric
        _BIAS_AVAILABLE = True
    except ImportError:
        _BIAS_AVAILABLE = False

    try:
        from deepeval.metrics import ToxicityMetric
        _TOXICITY_AVAILABLE = True
    except ImportError:
        _TOXICITY_AVAILABLE = False

    from deepeval.test_case import LLMTestCase
    from app.core.evaluator_provider.factory import get_evaluator_provider
    DEEPEVAL_AVAILABLE = True
except ImportError as e:
    DEEPEVAL_AVAILABLE = False
    logger.warning(f"DeepEval not available: {e}")

from ..runners.result import PipelineResult
from .result import MetricResult


class DeepEvalEvaluator:
    def __init__(self):
        if DEEPEVAL_AVAILABLE:
            self._provider = get_evaluator_provider()
            self._model = self._provider.get_deepeval_model()

    def evaluate(self, result: PipelineResult) -> MetricResult:
        metric_result = MetricResult(sample_id=result.sample_id, pipeline=result.pipeline)

        if not DEEPEVAL_AVAILABLE:
            metric_result.error = "deepeval not installed"
            return metric_result

        if not result.retrieved_contexts or not result.generated_answer:
            metric_result.error = "empty contexts or answer"
            return metric_result

        test_case = LLMTestCase(
            input=result.question,
            actual_output=result.generated_answer,
            expected_output=result.ground_truth_answer,
            retrieval_context=result.retrieved_contexts,
            context=result.retrieved_contexts,
        )

        scores = {}
        _run_metric(scores, "deepeval_faithfulness",
                    FaithfulnessMetric(threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_answer_relevancy",
                    AnswerRelevancyMetric(threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_hallucination",
                    HallucinationMetric(threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_contextual_precision",
                    ContextualPrecisionMetric(threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_contextual_recall",
                    ContextualRecallMetric(threshold=0.5, model=self._model), test_case)

        if _BIAS_AVAILABLE:
            _run_metric(scores, "deepeval_bias",
                        BiasMetric(threshold=0.5, model=self._model), test_case)
        if _TOXICITY_AVAILABLE:
            _run_metric(scores, "deepeval_toxicity",
                        ToxicityMetric(threshold=0.5, model=self._model), test_case)

        metric_result.scores = scores
        return metric_result


def _run_metric(scores: dict, key: str, metric, test_case) -> None:
    try:
        metric.measure(test_case)
        scores[key] = float(metric.score)
    except Exception as e:
        logger.warning(f"DeepEval metric '{key}' failed: {e}")
        scores[key] = None
