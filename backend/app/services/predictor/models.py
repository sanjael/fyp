from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PredictorMetadata(BaseModel):
    model_version: str
    prediction_latency_ms: float
    feature_version: str = "1.0"
    drift_flags: list[str] = Field(default_factory=list)
    confidence: str = "regression_output"

class InferenceResponse(BaseModel):
    trri: float
    metadata: PredictorMetadata
    shap_values: Optional[Dict[str, float]] = None
