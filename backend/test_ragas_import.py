print("1. Starting")

print("2. datasets")
from datasets import Dataset, Features, Value, Sequence

print("3. ragas")
from ragas import evaluate

print("4. ragas.metrics")
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

print("5. provider factory")
from app.core.evaluator_provider.factory import get_evaluator_provider

print("6. provider wrapper")
from app.core.evaluator_provider.base import ProviderLangchainWrapper

print("7. embedding_provider")
from app.services.embedding_provider import embeddings

print("8. SUCCESS")