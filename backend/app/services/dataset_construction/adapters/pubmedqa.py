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
        
        raw_meta = raw_record.get("metadata") or {}
        doc_metadata: Dict[str, Any] = {
            "dataset": "pubmedqa",
            "document_type": "academic_paper",
        }
        
        # Deterministically derive PMID and PubMed source URL from record_id if available (e.g. "pubmedqa_39085" -> "39085")
        id_str = str(record_id)
        pmid_candidate = id_str.replace("pubmedqa_", "").strip()
        if pmid_candidate.isdigit():
            doc_metadata["pmid"] = pmid_candidate
            doc_metadata["source_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_candidate}/"
        elif raw_meta.get("url"):
            doc_metadata["source_url"] = raw_meta["url"]
            
        if raw_meta.get("publication_year"):
            doc_metadata["publication_year"] = raw_meta["publication_year"]
            doc_metadata["year"] = raw_meta["publication_year"]
        
        return UnifiedDocumentSchema(
            record_id=id_str,
            query=query,
            ground_truth_answer=ground_truth_answer,
            documents=docs,
            metadata=doc_metadata
        )


