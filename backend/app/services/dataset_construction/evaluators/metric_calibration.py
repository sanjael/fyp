from typing import Dict
from .metric_validator import MetricValidator

class MetricCalibrator:
    def __init__(self):
        self.validator = MetricValidator()

    def calibrate(self, raw_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Validates and normalizes all raw metrics strictly into [0.0, 1.0].
        Different frameworks have different native scales.
        """
        calibrated = {}
        for name, score in raw_metrics.items():
            try:
                # 1. Validate
                valid_score = self.validator.validate(name, score)
                
                # 2. Scale
                # RAGAS natively outputs [0, 1]
                # DeepEval natively outputs [0, 1]
                # If there were metrics that output [1, 5], we would map them here:
                # valid_score = (valid_score - 1) / 4.0
                
                calibrated_score = max(0.0, min(1.0, valid_score))
                calibrated[name] = calibrated_score
                
            except ValueError as e:
                print(f"Calibration warning for {name}: {e}")
                
        return calibrated
