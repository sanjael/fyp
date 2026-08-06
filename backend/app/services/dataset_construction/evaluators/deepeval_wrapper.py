from typing import List, Dict
from langchain_core.documents import Document

try:
    from deepeval.test_case import LLMTestCase
    from ....core.evaluator_provider.factory import get_evaluator_provider
    try:
        from deepeval.metrics import FaithfulnessMetric
    except ImportError:
        from deepeval.metrics.ragas_metric import RagasFaithfulnessMetric as FaithfulnessMetric

    try:
        from deepeval.metrics import AnswerRelevancyMetric
    except ImportError:
        from deepeval.metrics.answer_relevancy import AnswerRelevancyMetric

    try:
        from deepeval.metrics import ContextualPrecisionMetric
    except ImportError:
        from deepeval.metrics.ragas_metric import RagasContextualRelevancyMetric as ContextualPrecisionMetric

    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False


class DeepEvalWrapper:
    """
    Wrapper for executing DeepEval metrics during offline dataset construction.
    """
    def __init__(self):
        if DEEPEVAL_AVAILABLE:
            self.provider = get_evaluator_provider()
            self.deepeval_llm = self.provider.get_deepeval_model()

    def compute_metrics(self, query: str, answer: str, docs: List[Document]) -> Dict[str, float]:
        if not DEEPEVAL_AVAILABLE:
            return {}
            
        contexts = [d.page_content for d in docs]
        test_case = LLMTestCase(
            input=query,
            actual_output=answer,
            expected_output=answer,
            retrieval_context=contexts
        )
        
        metrics = {}
        try:
            faith_metric = FaithfulnessMetric(threshold=0.5, model=self.deepeval_llm)
            faith_metric.measure(test_case)
            metrics["deepeval_faithfulness"] = faith_metric.score
            
            relevancy_metric = AnswerRelevancyMetric(threshold=0.5, model=self.deepeval_llm)
            relevancy_metric.measure(test_case)
            metrics["deepeval_answer_relevancy"] = relevancy_metric.score
            
            cp_metric = ContextualPrecisionMetric(threshold=0.5, model=self.deepeval_llm)
            cp_metric.measure(test_case)
            metrics["deepeval_contextual_precision"] = cp_metric.score
        except Exception as e:
            print(f"DeepEval failed: {e}")
            
        return metrics
