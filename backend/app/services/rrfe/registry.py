import time
from typing import List

from langchain_core.documents import Document

from .core.base_extractor import BaseFeatureExtractor
from .models import FeatureResult, ReliabilityFeatureVector, RRFEResult
from .extractors.temporal_freshness import TemporalFreshnessExtractor
from .extractors.temporal_availability import TemporalAvailabilityExtractor
from .extractors.source_credibility import SourceCredibilityExtractor
from .extractors.evidence_consistency import EvidenceConsistencyExtractor
from .extractors.evidence_sufficiency import EvidenceSufficiencyExtractor

# Fallback FeatureResult used when an extractor fails or validation fails.
# score=None signals that no valid score was produced.
# The predictor must handle None explicitly — never substitute 0.5.
_FALLBACK = FeatureResult(
    score=None,
    confidence=0.0,
    reason="Feature extraction failed (validation failed or extractor did not run)",
    evidence_source="Unavailable",
)


class FeatureRegistry:
    """Runs all registered extractors and assembles the RRFEResult."""

    def __init__(self) -> None:
        self._extractors: list[BaseFeatureExtractor] = []
        # Registration order determines feature vector column order
        self.register(TemporalFreshnessExtractor())
        self.register(TemporalAvailabilityExtractor())
        self.register(SourceCredibilityExtractor())
        self.register(EvidenceConsistencyExtractor())
        self.register(EvidenceSufficiencyExtractor())

    def register(self, extractor: BaseFeatureExtractor) -> None:
        self._extractors.append(extractor)

    def execute_all(self, query: str, docs: List[Document]) -> RRFEResult:
        start = time.perf_counter()
        explanations: dict[str, FeatureResult] = {}
        exec_meta: dict = {"failed_extractors": [], "skipped_extractors": []}

        for extractor in self._extractors:
            name = extractor.feature_name
            try:
                if not extractor.validate(query, docs):
                    exec_meta["skipped_extractors"].append(name)
                    explanations[name] = _FALLBACK
                    continue
                result: FeatureResult = extractor.extract(query, docs)
                explanations[name] = result
            except Exception as exc:
                exec_meta["failed_extractors"].append(f"{name}: {exc}")
                explanations[name] = FeatureResult(
                    score=None,
                    confidence=0.0,
                    reason=f"Feature extraction failed: {exc}",
                    evidence_source="Unavailable",
                )

        exec_meta["execution_time_ms"] = round(
            (time.perf_counter() - start) * 1000, 2
        )

        vector = ReliabilityFeatureVector(
            temporal_freshness=explanations["temporal_freshness"].score,
            temporal_availability=explanations["temporal_availability"].score,
            source_credibility=explanations["source_credibility"].score,
            evidence_consistency=explanations["evidence_consistency"].score,
            evidence_sufficiency=explanations["evidence_sufficiency"].score,
        )
        # Record which features have missing scores in metadata
        missing = [
            name for name, fr in explanations.items() if fr.score is None
        ]
        if missing:
            exec_meta["missing_feature_scores"] = missing

        return RRFEResult(
            features=vector,
            explanations=explanations,
            execution_metadata=exec_meta,
        )
