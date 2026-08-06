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
    from deepeval.test_case import LLMTestCase
    from app.core.evaluator_provider.factory import get_evaluator_provider

    try:
        from deepeval.metrics import FaithfulnessMetric
    except ImportError:
        from deepeval.metrics.ragas_metric import RagasFaithfulnessMetric as FaithfulnessMetric

    try:
        from deepeval.metrics import AnswerRelevancyMetric
    except ImportError:
        from deepeval.metrics.answer_relevancy import AnswerRelevancyMetric

    try:
        from deepeval.metrics import HallucinationMetric
    except ImportError:
        from deepeval.metrics.factual_consistency import FactualConsistencyMetric as HallucinationMetric

    try:
        from deepeval.metrics import ContextualPrecisionMetric
    except ImportError:
        from deepeval.metrics.ragas_metric import RagasContextualRelevancyMetric as ContextualPrecisionMetric

    try:
        from deepeval.metrics import ContextualRecallMetric
    except ImportError:
        from deepeval.metrics.ragas_metric import RagasContextRecallMetric as ContextualRecallMetric

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

    DEEPEVAL_AVAILABLE = True
except ImportError as e:
    DEEPEVAL_AVAILABLE = False
    logger.warning(f"DeepEval not available: {e}")

from ..runners.result import PipelineResult
from .result import MetricResult


def _instantiate_metric(metric_cls, threshold: float = 0.5, model=None):
    try:
        return metric_cls(threshold=threshold, model=model)
    except TypeError:
        try:
            instance = metric_cls(minimum_score=threshold, model_type="sentence_transformer")
        except TypeError:
            try:
                instance = metric_cls(minimum_score=threshold)
            except Exception as e:
                logger.warning(f"Failed to instantiate {metric_cls}: {e}")
                return None
        except Exception as e:
            logger.warning(f"Failed to instantiate {metric_cls}: {e}")
            return None
    except Exception as e:
        logger.warning(f"Failed to instantiate {metric_cls}: {e}")
        return None

    if hasattr(instance, "metrics") and getattr(instance, "metrics", None) is None:
        try:
            from ragas.metrics import context_precision
            instance.metrics = [context_precision]
        except Exception:
            pass

    if hasattr(instance, "metrics") and getattr(instance, "metrics", None) is not None:
        def custom_measure(test_case):
            from ragas import evaluate
            from ragas.llms import LangchainLLMWrapper
            from datasets import Dataset
            from app.services.embedding_provider import get_embeddings
            from app.core.evaluator_provider.factory import get_evaluator_provider

            provider = get_evaluator_provider()
            ragas_llm = LangchainLLMWrapper(provider.get_langchain_model())
            embeddings = get_embeddings()

            ctx = test_case.context if getattr(test_case, 'context', None) is not None else getattr(test_case, 'retrieval_context', [])
            data = {
                "ground_truths": [[test_case.expected_output]],
                "contexts": [ctx],
                "question": [test_case.input],
                "answer": [test_case.actual_output],
                "id": [[getattr(test_case, 'id', '1')]],
            }
            dataset = Dataset.from_dict(data)
            scores = evaluate(dataset, metrics=instance.metrics, llm=ragas_llm, embeddings=embeddings)
            key = list(scores.keys())[0]
            val = scores[key]
            score = float(val) if val is not None else 0.0
            instance.success = score >= getattr(instance, 'minimum_score', 0.5)
            instance.score = score
            return score

        instance.measure = custom_measure

    return instance


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
                    _instantiate_metric(FaithfulnessMetric, threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_answer_relevancy",
                    _instantiate_metric(AnswerRelevancyMetric, threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_hallucination",
                    _instantiate_metric(HallucinationMetric, threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_contextual_precision",
                    _instantiate_metric(ContextualPrecisionMetric, threshold=0.5, model=self._model), test_case)
        _run_metric(scores, "deepeval_contextual_recall",
                    _instantiate_metric(ContextualRecallMetric, threshold=0.5, model=self._model), test_case)

        if _BIAS_AVAILABLE:
            _run_metric(scores, "deepeval_bias",
                        _instantiate_metric(BiasMetric, threshold=0.5, model=self._model), test_case)
        if _TOXICITY_AVAILABLE:
            _run_metric(scores, "deepeval_toxicity",
                        _instantiate_metric(ToxicityMetric, threshold=0.5, model=self._model), test_case)

        metric_result.scores = scores
        return metric_result


def _run_metric(scores: dict, key: str, metric, test_case) -> None:
    if metric is None:
        scores[key] = None
        return
    try:
        metric.measure(test_case)
        scores[key] = float(metric.score)
    except Exception as e:
        logger.warning(f"DeepEval metric '{key}' failed: {e}")
        scores[key] = None
