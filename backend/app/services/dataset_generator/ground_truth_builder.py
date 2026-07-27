from typing import Dict
import logging
from .models import GroundTruthResult

logger = logging.getLogger("ragguard.ground_truth")

# ---------------------------------------------------------------------------
# Default RRT weights — documented rationale
# ---------------------------------------------------------------------------
# RRT = Retrieval Reliability Target, the ground-truth label for TRRI training.
#
# Weight rationale (can be overridden via constructor):
#   ragas_context_precision  0.6 — Primary signal: measures whether retrieved
#       chunks are relevant to the question. Directly reflects retrieval quality,
#       which is the core concern of TRRI.
#   deepeval_faithfulness    0.4 — Secondary signal: measures whether the answer
#       is grounded in the retrieved context. Captures generation reliability
#       conditioned on retrieval.
#
# These weights were chosen to weight retrieval quality (the TRRI target) more
# heavily than generation quality. They are configurable and must be logged
# in every experiment to ensure reproducibility.
# ---------------------------------------------------------------------------
DEFAULT_RRT_WEIGHTS: Dict[str, float] = {
    "ragas_context_precision": 0.6,
    "deepeval_faithfulness":   0.4,
    "manual_expert_score":     1.0,   # Override: if present, replaces computed RRT
}


class GroundTruthBuilder:
    def __init__(
        self,
        strategy: str = "weighted_mean",
        weights: Dict[str, float] = None,
    ):
        self.strategy = strategy
        # Use provided weights or fall back to documented defaults
        self.weights = weights if weights is not None else dict(DEFAULT_RRT_WEIGHTS)
        # Log weights at construction time for experiment reproducibility
        logger.info(
            "GroundTruthBuilder initialised. "
            f"strategy={self.strategy} "
            f"weights={self.weights}"
        )

    def build_rrt(self, raw_metrics: Dict[str, float]) -> GroundTruthResult:
        if not raw_metrics:
            return GroundTruthResult(rrt=0.0, confidence=0.0, strategy=self.strategy)

        if self.strategy == "weighted_mean":
            # Manual expert score overrides computed RRT when present
            if "manual_expert_score" in raw_metrics:
                logger.debug("manual_expert_score present — using manual override")
                return GroundTruthResult(
                    rrt=raw_metrics["manual_expert_score"],
                    confidence=1.0,
                    strategy="manual_override",
                )

            total_weight = 0.0
            weighted_sum = 0.0
            used_metrics = {}

            for metric, score in raw_metrics.items():
                w = self.weights.get(metric, 0.0)
                if w == 0.0:
                    continue
                total_weight += w
                weighted_sum += score * w
                used_metrics[metric] = {"score": score, "weight": w}

            rrt = weighted_sum / total_weight if total_weight > 0 else 0.0
            confidence = len(used_metrics) / max(1, len(
                [k for k, v in self.weights.items() if v > 0 and k != "manual_expert_score"]
            ))

            logger.debug(
                f"RRT computed: rrt={rrt:.4f} confidence={confidence:.4f} "
                f"used_metrics={used_metrics} weights={self.weights}"
            )

            return GroundTruthResult(
                rrt=rrt,
                confidence=confidence,
                strategy=self.strategy,
            )

        return GroundTruthResult(rrt=0.0, confidence=0.0, strategy="unknown")
