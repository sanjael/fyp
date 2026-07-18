from typing import List, Dict
from langchain_core.documents import Document
from .evaluators.base import BaseEvaluator
from .evaluators.ragas_eval import RagasContextPrecisionEvaluator
from .evaluators.deepeval_eval import DeepEvalFaithfulnessEvaluator
from .evaluators.manual_eval import ManualExpertEvaluator

class EvaluatorRunner:
    def __init__(self):
        self._evaluators: List[BaseEvaluator] = [
            RagasContextPrecisionEvaluator(),
            DeepEvalFaithfulnessEvaluator(),
            ManualExpertEvaluator()
        ]
        
    def run_all(self, query: str, docs: List[Document]) -> Dict[str, float]:
        raw_metrics = {}
        for evaluator in self._evaluators:
            try:
                score = evaluator.evaluate(query, docs)
                if score is not None:
                    raw_metrics[evaluator.name] = score
            except Exception as e:
                # Log error
                print(f"Evaluator {evaluator.name} failed: {e}")
                
        return raw_metrics
