import uuid
from typing import Dict, Any
from .base import BaseAdapter
from ..models import UnifiedDocumentSchema

class PubMedQAAdapter(BaseAdapter):
    def extract(self, raw_record: Dict[str, Any]) -> UnifiedDocumentSchema:
        query = raw_record.get("question") or raw_record.get("QUESTION") or ""
        ground_truth_answer = raw_record.get("response") or raw_record.get("LONG_ANSWER") or raw_record.get("long_answer") or ""
        docs = raw_record.get("documents") or raw_record.get("CONTEXTS") or raw_record.get("contexts") or []
        record_id = raw_record.get("id") or raw_record.get("pubid") or str(uuid.uuid4())
        
        return UnifiedDocumentSchema(
            record_id=str(record_id),
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata={"dataset": "pubmedqa"}
        )
