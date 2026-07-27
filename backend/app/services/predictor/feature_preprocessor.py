import numpy as np
from typing import Optional

# Ordered feature names — must match XGBoost training column order
FEATURE_NAMES = [
    "temporal_freshness",
    "temporal_availability",
    "source_credibility",
    "evidence_consistency",
    "evidence_sufficiency",
]


class MissingFeatureError(ValueError):
    """
    Raised when one or more RRFE features have score=None.
    The predictor must not substitute a neutral default for missing features.
    """
    pass


class FeaturePreprocessor:
    """
    Converts the RRFE feature dict into a strictly-ordered numpy array
    for XGBoost inference.

    Column order: [tff, taf, scf, ecf, esf]  (5 features)
    All values are clamped to [0, 1] before inference.
    Raises MissingFeatureError if any feature score is None.
    """

    def get_missing_features(self, rrfe_features: dict) -> list[str]:
        return [
            name for name in FEATURE_NAMES
            if rrfe_features.get(name) is None
        ]

    def transform(self, rrfe_features: dict) -> np.ndarray:
        missing = self.get_missing_features(rrfe_features)
        if missing:
            raise MissingFeatureError(
                f"Cannot predict TRRI: the following RRFE features have no valid score: "
                f"{missing}. "
                f"Substituting 0.5 is scientifically invalid. "
                f"Investigate why these extractors failed before running evaluation."
            )
        row = [
            max(0.0, min(1.0, float(rrfe_features[name])))
            for name in FEATURE_NAMES
        ]
        return np.array([row])
