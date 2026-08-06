import uuid
from typing import Dict, Any
from .base import BaseAdapter
from ..models import UnifiedDocumentSchema

class TechQAAdapter(BaseAdapter):
    def extract(self, raw_record: Dict[str, Any]) -> UnifiedDocumentSchema:
        query = raw_record.get("question_text", "")
        ground_truth_answer = raw_record.get("answer", "")
        docs = [d.get("text", "") for d in raw_record.get("documents", []) if isinstance(d, dict)]
        record_id = raw_record.get("id", str(uuid.uuid4()))
        
        raw_meta = raw_record.get("metadata") or {}
        doc_metadata: Dict[str, Any] = {
            "dataset": "techqa",
            "document_type": "technical_documentation",
        }
        if raw_meta.get("url"):
            doc_metadata["source_url"] = raw_meta["url"]

        return UnifiedDocumentSchema(
            record_id=str(record_id),
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata=doc_metadata
        )


