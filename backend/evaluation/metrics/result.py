"""Metric result container shared by RAGAS and DeepEval evaluators."""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class MetricResult:
    sample_id: str
    pipeline: str
    # All computed metric scores keyed by metric name
    scores: Dict[str, Optional[float]] = field(default_factory=dict)
    error: Optional[str] = None
