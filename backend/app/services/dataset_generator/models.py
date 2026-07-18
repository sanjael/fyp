from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class DatasetSample(BaseModel):
    session_id: str
    query: str
    document_ids: List[str]
    retrieved_metadata: Dict[str, Any] = Field(default_factory=dict)
    tff: float
    scf: float
    ecf: float
    esf: float
    raw_metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GroundTruthResult(BaseModel):
    rrt: float
    confidence: float
    strategy: str
