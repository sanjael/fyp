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
        
        raw_meta = raw_record.get("metadata") or {}
        doc_metadata: Dict[str, Any] = {
            "dataset": "hotpotqa",
            "document_type": "official_report",
        }
        
        if raw_meta.get("url"):
            doc_metadata["source_url"] = raw_meta["url"]
        if raw_meta.get("publication_year"):
            doc_metadata["publication_year"] = raw_meta["publication_year"]
            doc_metadata["year"] = raw_meta["publication_year"]
        
        return UnifiedDocumentSchema(
            record_id=str(record_id),
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata=doc_metadata
        )


