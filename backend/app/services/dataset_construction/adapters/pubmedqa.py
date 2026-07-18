import uuid
from typing import Dict, Any
from .base import BaseAdapter
from ..models import UnifiedDocumentSchema

class PubMedQAAdapter(BaseAdapter):
    def extract(self, raw_record: Dict[str, Any]) -> UnifiedDocumentSchema:
        query = raw_record.get("QUESTION", "")
        ground_truth_answer = raw_record.get("LONG_ANSWER", "")
        
        # PubMedQA 'CONTEXTS' is a list of context strings
        docs = raw_record.get("CONTEXTS", [])
        
        record_id = raw_record.get("pubid", str(uuid.uuid4()))
        
        return UnifiedDocumentSchema(
            record_id=str(record_id),
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata={"dataset": "pubmedqa"}
        )
