import pytest
from app.services.predictor.inference import predictor_engine
from app.services.predictor.models import InferenceResponse

def test_trri_prediction_missing_features():
    # Scientific Integrity test: When features have None, returns PredictionUnavailable (trri=None, is_available=False)
    features_with_missing = {
        "temporal_freshness": None,
        "temporal_availability": 1.0,
        "source_credibility": 0.8,
        "evidence_consistency": 0.9,
        "evidence_sufficiency": 0.7,
    }
    response = predictor_engine.predict(features_with_missing)
    assert isinstance(response, InferenceResponse)
    assert response.trri is None
    assert response.is_available is False
    assert "temporal_freshness" in response.missing_features
    assert "Prediction unavailable" in response.reason
