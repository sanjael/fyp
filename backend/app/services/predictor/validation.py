import math
from .config import config
from .models import PredictorMetadata

class PredictionValidator:
    def validate_prediction(self, trri: float) -> tuple[float, list[str]]:
        """
        Validates the predicted TRRI.
        Returns the validated score and a list of drift flags/warnings.
        We explicitly do NOT silently clip unless it's a minor float precision issue.
        """
        flags = []
        
        # Check NaN
        if math.isnan(trri):
            flags.append("NaN_prediction_fallback")
            return 0.5, flags
            
        # Check out of bounds (model drift / failure)
        if trri < config.TRRI_MIN - 1e-4 or trri > config.TRRI_MAX + 1e-4:
            flags.append(f"out_of_bounds_prediction: {trri}")
            
        # Hard clamp for safety but only after logging the flag
        safe_trri = max(config.TRRI_MIN, min(config.TRRI_MAX, trri))
        
        # Monitor for edge hugging (drift indicator)
        if safe_trri > 0.99:
            flags.append("extreme_high_confidence")
        elif safe_trri < 0.01:
            flags.append("extreme_low_confidence")
            
        return safe_trri, flags

    def build_metadata(self, latency: float, version: str, drift_flags: list[str]) -> PredictorMetadata:
        return PredictorMetadata(
            model_version=version,
            prediction_latency_ms=latency,
            drift_flags=drift_flags
        )
