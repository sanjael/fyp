from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class DatasetSample(BaseModel):
    session_id: str
    query: str
    document_ids: List[str]
    retrieved_metadata: Dict[str, Any] = Field(default_factory=dict)
    tff: Optional[float] = None
    taf: Optional[float] = None
    scf: Optional[float] = None
    ecf: Optional[float] = None
    esf: Optional[float] = None
    raw_metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GroundTruthResult(BaseModel):
    rrt: float
    confidence: float
    strategy: str
