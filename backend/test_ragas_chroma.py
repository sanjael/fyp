print("1")

from ragas import evaluate
print("2")

import chromadb
print("3")

from app.services.embedding_provider import embeddings  # clean — no chromadb in this path
print("4")
