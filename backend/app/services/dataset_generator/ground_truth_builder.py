from typing import Dict
from .models import GroundTruthResult

class GroundTruthBuilder:
    def __init__(self, strategy: str = "weighted_mean"):
        self.strategy = strategy
        # Configurable weights for different metrics
        self.weights = {
            "ragas_context_precision": 0.6,
            "deepeval_faithfulness": 0.4,
            "manual_expert_score": 1.0  # If manual exists, it can override or dominate
        }
        
    def build_rrt(self, raw_metrics: Dict[str, float]) -> GroundTruthResult:
        if not raw_metrics:
            return GroundTruthResult(rrt=0.0, confidence=0.0, strategy=self.strategy)
            
        if self.strategy == "weighted_mean":
            total_weight = 0.0
            weighted_sum = 0.0
            
            # Check if manual expert score exists, if so it overrides
            if "manual_expert_score" in raw_metrics:
                return GroundTruthResult(
                    rrt=raw_metrics["manual_expert_score"], 
                    confidence=1.0, 
                    strategy="manual_override"
                )
                
            for metric, score in raw_metrics.items():
                w = self.weights.get(metric, 1.0)
                total_weight += w
                weighted_sum += score * w
                
            rrt = weighted_sum / total_weight if total_weight > 0 else 0.0
            confidence = len(raw_metrics) / len(self.weights)
            
            return GroundTruthResult(rrt=rrt, confidence=confidence, strategy=self.strategy)
            
        # Default fallback
        return GroundTruthResult(rrt=0.0, confidence=0.0, strategy="unknown")
