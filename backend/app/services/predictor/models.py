from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PredictorMetadata(BaseModel):
    model_version: str
    prediction_latency_ms: float
    feature_version: str = "1.0"
    drift_flags: List[str] = Field(default_factory=list)
    confidence: str = "regression_output"

class InferenceResponse(BaseModel):
    trri: Optional[float] = None
    is_available: bool = True
    missing_features: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    metadata: PredictorMetadata
    shap_values: Optional[Dict[str, float]] = None

