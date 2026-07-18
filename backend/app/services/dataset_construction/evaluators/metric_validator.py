import math

class MetricValidator:
    def validate(self, metric_name: str, score: float) -> float:
        """
        Validates LLM-as-a-judge scores. 
        Rejects NaNs and aggressively out-of-bounds scores before calibration.
        """
        if score is None or math.isnan(score):
            raise ValueError(f"Invalid Score: {metric_name} returned NaN.")
            
        if score < -100 or score > 100:
            raise ValueError(f"Score {score} for {metric_name} is wildly out of expected bounds.")
            
        return score
