from typing import Any, Dict
from pydantic import BaseModel, Field

class ReliabilityFeatureVector(BaseModel):
    temporal_freshness: float = Field(..., ge=0.0, le=1.0)
    source_credibility: float = Field(..., ge=0.0, le=1.0)
    evidence_consistency: float = Field(..., ge=0.0, le=1.0)
    evidence_sufficiency: float = Field(..., ge=0.0, le=1.0)

class RRFEResult(BaseModel):
    features: ReliabilityFeatureVector
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
