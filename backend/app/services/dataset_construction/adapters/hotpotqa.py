import uuid
from typing import Dict, Any
from .base import BaseAdapter
from ..models import UnifiedDocumentSchema

class HotpotQAAdapter(BaseAdapter):
    def extract(self, raw_record: Dict[str, Any]) -> UnifiedDocumentSchema:
        query = raw_record.get("question", "")
        ground_truth_answer = raw_record.get("response", "")
        
        # Ragbench normalizes documents to a list of strings
        docs = raw_record.get("documents", [])
                
        record_id = raw_record.get("id", str(uuid.uuid4()))
        
        return UnifiedDocumentSchema(
            record_id=record_id,
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata={"dataset": "hotpotqa"}
        )
