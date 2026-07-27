"""
Shared result schema for both RAGGuard-TR and Baseline pipeline runners.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PipelineResult:
    sample_id: str
    question: str
    ground_truth_answer: str
    gold_contexts: List[str]

    # Retrieval
    retrieved_contexts: List[str] = field(default_factory=list)
    retrieved_doc_metadata: List[dict] = field(default_factory=dict)

    # Generation
    generated_answer: str = ""

    # RAGGuard-TR specific (None for baseline)
    rrfe_features: Optional[Dict[str, float]] = None
    rrfe_explanations: Optional[Dict[str, dict]] = None
    trri: Optional[float] = None
    risk_level: Optional[str] = None
    predictor_model_version: Optional[str] = None

    # Timing
    retrieval_latency_ms: float = 0.0
    rrfe_latency_ms: float = 0.0
    predictor_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

    # Pipeline identifier
    pipeline: str = "unknown"   # "ragguard_tr" | "baseline"
    dataset_name: str = ""
    error: Optional[str] = None
