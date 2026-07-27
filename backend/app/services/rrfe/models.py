from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Per-feature explainability envelope
# ---------------------------------------------------------------------------

class FeatureResult(BaseModel):
    """Returned by every BaseFeatureExtractor.extract() call.

    score=None means the extractor could not produce a valid score.
    The predictor must handle None scores explicitly — never substitute 0.5.
    """
    score: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Normalised reliability score [0, 1], or None if unavailable"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the score [0, 1]")
    reason: str = Field(..., description="Human-readable explanation of the score")
    evidence_source: str = Field(..., description="Where the data came from (e.g. 'Document Metadata')")


# ---------------------------------------------------------------------------
# Temporal Availability (new feature)
# ---------------------------------------------------------------------------

TemporalAvailabilityStatus = Literal["Available", "Estimated", "Unknown"]

class TemporalAvailabilityResult(FeatureResult):
    """Extended result for the Temporal Availability extractor."""
    availability_status: TemporalAvailabilityStatus = Field(
        ..., description="Whether the publication date can be identified"
    )


# ---------------------------------------------------------------------------
# Feature vector passed to the XGBoost predictor
# ---------------------------------------------------------------------------

class ReliabilityFeatureVector(BaseModel):
    """Five-feature input vector for the TRRI predictor.

    Each field is Optional[float] — None means the extractor could not
    produce a valid score. The predictor must reject vectors with None
    values rather than substituting a neutral default.
    """
    temporal_freshness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    temporal_availability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_credibility: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_consistency: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_sufficiency: Optional[float] = Field(default=None, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Full RRFE result returned by the engine
# ---------------------------------------------------------------------------

class RRFEResult(BaseModel):
    features: ReliabilityFeatureVector
    # Explainability: one FeatureResult per extractor, keyed by feature_name
    explanations: Dict[str, FeatureResult] = Field(default_factory=dict)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
