import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple

from langchain_core.documents import Document

from .core.base_extractor import BaseFeatureExtractor
from .models import FeatureResult, ReliabilityFeatureVector, RRFEResult
from .extractors.temporal_freshness import TemporalFreshnessExtractor
from .extractors.temporal_availability import TemporalAvailabilityExtractor
from .extractors.source_credibility import SourceCredibilityExtractor
from .extractors.evidence_consistency import EvidenceConsistencyExtractor
from .extractors.evidence_sufficiency import EvidenceSufficiencyExtractor

_FALLBACK = FeatureResult(
    score=None,
    confidence=0.0,
    reason="Feature extraction failed (validation failed or extractor did not run)",
    evidence_source="Unavailable",
)


class FeatureRegistry:
    """Runs all registered extractors concurrently and assembles the RRFEResult."""

    def __init__(self) -> None:
        self._extractors: List[BaseFeatureExtractor] = []
        self.register(TemporalFreshnessExtractor())
        self.register(TemporalAvailabilityExtractor())
        self.register(SourceCredibilityExtractor())
        self.register(EvidenceConsistencyExtractor())
        self.register(EvidenceSufficiencyExtractor())

    def register(self, extractor: BaseFeatureExtractor) -> None:
        self._extractors.append(extractor)

    def _run_single_extractor(self, extractor: BaseFeatureExtractor, query: str, docs: List[Document]) -> tuple[str, FeatureResult, Optional[str]]:
        name = extractor.feature_name
        try:
            if not extractor.validate(query, docs):
                return name, _FALLBACK, "skipped"
            result: FeatureResult = extractor.extract(query, docs)
            return name, result, None
        except Exception as exc:
            err_result = FeatureResult(
                score=None,
                confidence=0.0,
                reason=f"Feature extraction failed: {exc}",
                evidence_source="Unavailable",
            )
            return name, err_result, str(exc)

    def execute_all(self, query: str, docs: List[Document]) -> RRFEResult:
        start = time.perf_counter()
        explanations: Dict[str, FeatureResult] = {}
        exec_meta: Dict = {"failed_extractors": [], "skipped_extractors": []}

        # Parallelize independent feature extractors using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self._run_single_extractor, ext, query, docs)
                for ext in self._extractors
            ]
            for future in as_completed(futures):
                name, result, err = future.result()
                explanations[name] = result
                if err == "skipped":
                    exec_meta["skipped_extractors"].append(name)
                elif err is not None:
                    exec_meta["failed_extractors"].append(f"{name}: {err}")

        exec_meta["execution_time_ms"] = round((time.perf_counter() - start) * 1000, 2)

        vector = ReliabilityFeatureVector(
            temporal_freshness=explanations["temporal_freshness"].score,
            temporal_availability=explanations["temporal_availability"].score,
            source_credibility=explanations["source_credibility"].score,
            evidence_consistency=explanations["evidence_consistency"].score,
            evidence_sufficiency=explanations["evidence_sufficiency"].score,
        )
        missing = [name for name, fr in explanations.items() if fr.score is None]
        if missing:
            exec_meta["missing_feature_scores"] = missing

        return RRFEResult(
            features=vector,
            explanations=explanations,
            execution_metadata=exec_meta,
        )
