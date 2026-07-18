import numpy as np
from typing import Dict

class EvaluatorReliabilityEstimator:
    def __init__(self):
        # Base historical confidence weights
        self.base_weights = {
            "ragas": 0.6,
            "deepeval": 0.4
        }
        
    def estimate_reliability(self, calibrated_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Dynamically adjusts evaluator weights based on missing-rates, variance, 
        and cross-evaluator agreement.
        """
        ragas_scores = [v for k, v in calibrated_metrics.items() if "ragas" in k]
        deepeval_scores = [v for k, v in calibrated_metrics.items() if "deepeval" in k]
        
        # 1. Missing-rate penalization
        ragas_weight = self.base_weights["ragas"] if ragas_scores else 0.0
        deepeval_weight = self.base_weights["deepeval"] if deepeval_scores else 0.0
        
        # 2. Variance penalization (if an evaluator contradicts itself heavily across its own metrics)
        if ragas_scores and len(ragas_scores) > 1 and np.var(ragas_scores) > 0.15:
            ragas_weight *= 0.8
            
        if deepeval_scores and len(deepeval_scores) > 1 and np.var(deepeval_scores) > 0.15:
            deepeval_weight *= 0.8
            
        # 3. Agreement reward (if they agree, they are both highly reliable)
        if ragas_scores and deepeval_scores:
            ragas_mean = np.mean(ragas_scores)
            deepeval_mean = np.mean(deepeval_scores)
            if abs(ragas_mean - deepeval_mean) < 0.1:
                ragas_weight *= 1.1
                deepeval_weight *= 1.1
                
        # Normalize weights
        total = ragas_weight + deepeval_weight
        if total > 0:
            return {
                "ragas": ragas_weight / total,
                "deepeval": deepeval_weight / total
            }
        else:
            return {"ragas": 0.0, "deepeval": 0.0}
