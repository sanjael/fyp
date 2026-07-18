from typing import List, Dict
from langchain_core.documents import Document

try:
    from datasets import Dataset, Features, Value, Sequence
    from ragas import evaluate
    from ragas.metrics import context_precision, faithfulness, answer_relevancy
    from ....core.evaluator_provider.factory import get_evaluator_provider
    from ....core.evaluator_provider.base import ProviderLangchainWrapper
    from ....services.embedding_engine import embeddings
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False

class RagasWrapper:
    """
    Wrapper for executing RAGAS metrics during offline dataset construction.
    """
    def __init__(self):
        if RAGAS_AVAILABLE:
            self.provider = get_evaluator_provider()
            self.llm = ProviderLangchainWrapper(provider=self.provider, underlying=self.provider.get_langchain_model())
        
    def compute_metrics(self, query: str, answer: str, docs: List[Document]) -> Dict[str, float]:
        if not RAGAS_AVAILABLE:
            return {}
            
        contexts = [d.page_content for d in docs]
        data = {
            "question": [query],
            "contexts": [contexts],
            "answer": [answer],
            "ground_truth": [answer]
        }
        
        try:
            features = Features({
                "question": Value("string"),
                "contexts": Sequence(Value("string")),
                "answer": Value("string"),
                "ground_truth": Value("string")
            })
            dataset = Dataset.from_dict(data, features=features)
            result = evaluate(
                dataset,
                metrics=[context_precision, faithfulness, answer_relevancy],
                llm=self.llm,
                embeddings=embeddings
            )
            # Handle possible missing keys or NaNs gracefully
            return {
                "ragas_context_precision": float(result.get("context_precision", 0.0)),
                "ragas_faithfulness": float(result.get("faithfulness", 0.0)),
                "ragas_answer_relevancy": float(result.get("answer_relevancy", 0.0))
            }
        except Exception as e:
            print(f"Ragas evaluation failed: {e}")
            return {}
