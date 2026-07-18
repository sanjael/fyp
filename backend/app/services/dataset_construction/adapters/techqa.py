import uuid
from typing import Dict, Any
from .base import BaseAdapter
from ..models import UnifiedDocumentSchema

class TechQAAdapter(BaseAdapter):
    def extract(self, raw_record: Dict[str, Any]) -> UnifiedDocumentSchema:
        query = raw_record.get("question_text", "")
        ground_truth_answer = raw_record.get("answer", "") # TechQA answers format varies
        
        # TechQA documents can be large, we grab the provided snippet or document text
        docs = []
        for doc in raw_record.get("documents", []):
            docs.append(doc.get("text", ""))
            
        record_id = raw_record.get("id", str(uuid.uuid4()))
        
        return UnifiedDocumentSchema(
            record_id=str(record_id),
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata={"dataset": "techqa"}
        )
