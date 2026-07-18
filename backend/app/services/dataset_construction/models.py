from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class UnifiedDocumentSchema(BaseModel):
    record_id: str
    query: str
    ground_truth_answer: str
    documents: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinalDatasetRow(BaseModel):
    session_id: str
    dataset_name: str
    query: str
    ground_truth_answer: str
    retrieved_chunk_ids: List[str]
    rrfe_features: Dict[str, float]
    raw_metrics: Dict[str, float]
    calibrated_metrics: Dict[str, float]
    evaluator_reliability: Dict[str, float]
    rrt: float
    processing_metadata: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
