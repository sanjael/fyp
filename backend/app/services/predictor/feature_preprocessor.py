import numpy as np

class FeaturePreprocessor:
    def transform(self, rrfe_features: dict) -> np.ndarray:
        """
        Takes raw dictionary of RRFE features and normalizes to a rigid numpy array.
        Expected order: [tff, scf, ecf, esf]
        """
        # Strictly enforce bounds and structure before inference
        tff = max(0.0, min(1.0, float(rrfe_features.get("temporal_freshness", 0.5))))
        scf = max(0.0, min(1.0, float(rrfe_features.get("source_credibility", 0.5))))
        ecf = max(0.0, min(1.0, float(rrfe_features.get("evidence_consistency", 0.5))))
        esf = max(0.0, min(1.0, float(rrfe_features.get("evidence_sufficiency", 0.5))))
        
        # XGBoost expects 2D array for single inference: shape (1, 4)
        return np.array([[tff, scf, ecf, esf]])
