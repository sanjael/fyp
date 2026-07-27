"""
RAGGuard-TR pipeline runner.

Reuses the existing production modules without modification:
  - embedding_engine.search_documents / add_documents_to_chroma (retriever)
  - rrfe_engine.extract_features       (RRFE)
  - predictor_engine.predict           (TRRI)
  - llm_service.generate_answer        (LLM)

ChromaDB isolation
------------------
Each benchmark sample uses a unique, ephemeral collection named
  eval_rg_<sample_id>
The collection is deleted after the sample is processed, preventing
cross-sample retrieval contamination.
"""
import sys
import os
import time
import logging
from typing import List

from langchain_core.documents import Document

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.embedding_provider import get_embeddings
from app.services.vector_store import get_chroma_client as _get_chroma_client, add_documents_to_chroma, search_documents
from app.services.llm_service import generate_answer
from app.services.rrfe.engine import rrfe_engine
from app.services.predictor.inference import predictor_engine
from app.services.document_processor import chunk_document
from langchain_community.vectorstores import Chroma

from ..datasets.base import BenchmarkSample
from .result import PipelineResult

logger = logging.getLogger("eval.ragguard_tr")


def _collection_name(sample_id: str) -> str:
    """Deterministic, safe collection name for a single evaluation sample."""
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in sample_id)
    return f"eval_rg_{safe}"[:63]   # ChromaDB max collection name length


class RAGGuardTRRunner:
    """Runs the full RAGGuard-TR pipeline for a single benchmark sample."""

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def _get_isolated_store(self, collection_name: str) -> Chroma:
        """Return a Chroma vector store bound to an isolated collection."""
        return Chroma(
            client=_get_chroma_client(),
            collection_name=collection_name,
            embedding_function=get_embeddings(),
        )

    def _delete_collection(self, collection_name: str) -> None:
        """Delete the ephemeral collection to prevent cross-sample contamination."""
        try:
            _get_chroma_client().delete_collection(collection_name)
            logger.debug(f"Deleted isolated collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Could not delete collection {collection_name}: {e}")

    def _index_sample_docs(self, docs: List[str], store: Chroma) -> None:
        """Index supporting documents into the isolated collection."""
        chunks: List[Document] = []
        for text in docs:
            if text and text.strip():
                chunks.extend(chunk_document(text, filename="eval_doc.txt"))
        if chunks:
            store.add_documents(chunks)

    def run(self, sample: BenchmarkSample) -> PipelineResult:
        result = PipelineResult(
            sample_id=sample.sample_id,
            question=sample.question,
            ground_truth_answer=sample.ground_truth_answer,
            gold_contexts=sample.gold_contexts,
            pipeline="ragguard_tr",
            dataset_name=sample.dataset_name,
        )
        t_total_start = time.perf_counter()
        collection_name = _collection_name(sample.sample_id)

        try:
            # 1. Create isolated collection and index supporting documents
            store = self._get_isolated_store(collection_name)
            self._index_sample_docs(sample.supporting_documents, store)

            # 2. Retrieve from the isolated collection only
            t0 = time.perf_counter()
            results = store.similarity_search_with_score(sample.question, k=self.top_k)
            result.retrieval_latency_ms = (time.perf_counter() - t0) * 1000
            docs = [doc for doc, _ in results]
            result.retrieved_contexts = [doc.page_content for doc in docs]
            result.retrieved_doc_metadata = [doc.metadata for doc in docs]

            # 3. RRFE
            t0 = time.perf_counter()
            rrfe_result = rrfe_engine.extract_features(sample.question, docs)
            result.rrfe_latency_ms = (time.perf_counter() - t0) * 1000
            result.rrfe_features = rrfe_result.features.model_dump()
            result.rrfe_explanations = {
                name: {
                    "score": fr.score,
                    "confidence": fr.confidence,
                    "reason": fr.reason,
                    "evidence_source": fr.evidence_source,
                }
                for name, fr in rrfe_result.explanations.items()
            }

            # 4. TRRI prediction
            t0 = time.perf_counter()
            inference = predictor_engine.predict(rrfe_result.features.model_dump())
            result.predictor_latency_ms = (time.perf_counter() - t0) * 1000
            result.trri = inference.trri
            result.predictor_model_version = inference.metadata.model_version
            if inference.trri is None:
                result.risk_level = "unavailable"
            elif inference.trri < 0.5:
                result.risk_level = "high"
            elif inference.trri < 0.8:
                result.risk_level = "medium"
            else:
                result.risk_level = "low"

            # 5. Generate answer
            context_text = "\n\n".join(result.retrieved_contexts)
            t0 = time.perf_counter()
            result.generated_answer = generate_answer(sample.question, context_text)
            result.generation_latency_ms = (time.perf_counter() - t0) * 1000

        except Exception as e:
            result.error = str(e)
            logger.error(f"RAGGuard-TR pipeline failed for {sample.sample_id}: {e}")
        finally:
            # Always delete the isolated collection — even on failure
            self._delete_collection(collection_name)

        result.total_latency_ms = (time.perf_counter() - t_total_start) * 1000
        return result
