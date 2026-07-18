import uuid
from typing import List, Dict, Any
from langchain_core.documents import Document
from ..rrfe.models import ReliabilityFeatureVector
from .models import DatasetSample

class SampleBuilder:
    def build(self, query: str, docs: List[Document], rrfe_vector: ReliabilityFeatureVector, raw_metrics: Dict[str, float]) -> DatasetSample:
        # Extract chunk IDs from metadata
        doc_ids = [doc.metadata.get("chunk_id", f"chk-{i}") for i, doc in enumerate(docs)]
        
        # Simple metadata tracking
        retrieved_metadata = {
            "top_k": len(docs)
        }
        
        return DatasetSample(
            session_id=str(uuid.uuid4()),
            query=query,
            document_ids=doc_ids,
            retrieved_metadata=retrieved_metadata,
            tff=rrfe_vector.temporal_freshness,
            scf=rrfe_vector.source_credibility,
            ecf=rrfe_vector.evidence_consistency,
            esf=rrfe_vector.evidence_sufficiency,
            raw_metrics=raw_metrics
        )
