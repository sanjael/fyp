import time
from typing import List, Dict, Type
from langchain_core.documents import Document
from .core.base_extractor import BaseFeatureExtractor
from .models import ReliabilityFeatureVector, RRFEResult
from .extractors.temporal_freshness import TemporalFreshnessExtractor
from .extractors.source_credibility import SourceCredibilityExtractor
from .extractors.evidence_consistency import EvidenceConsistencyExtractor
from .extractors.evidence_sufficiency import EvidenceSufficiencyExtractor

class FeatureRegistry:
    def __init__(self):
        self._extractors: List[BaseFeatureExtractor] = []
        # Pre-register default extractors
        self.register(TemporalFreshnessExtractor())
        self.register(SourceCredibilityExtractor())
        self.register(EvidenceConsistencyExtractor())
        self.register(EvidenceSufficiencyExtractor())
        
    def register(self, extractor: BaseFeatureExtractor):
        self._extractors.append(extractor)
        
    def execute_all(self, query: str, docs: List[Document]) -> RRFEResult:
        start_time = time.time()
        features = {}
        metadata = {"failed_extractors": [], "missing_metadata_features": []}
        
        for extractor in self._extractors:
            name = extractor.feature_name
            try:
                if extractor.validate(query, docs):
                    score = extractor.extract(query, docs)
                else:
                    # Explicit well-defined fallback when metadata is missing
                    metadata["missing_metadata_features"].append(name)
                    # For simplicity here we use 0.5 (or we could fetch from config)
                    score = 0.5
                features[name] = score
            except Exception as e:
                print(f"Extractor {name} failed: {e}")
                metadata["failed_extractors"].append(name)
                features[name] = 0.5
                
        metadata["execution_time_ms"] = (time.time() - start_time) * 1000
        
        # Build the vector safely
        vector = ReliabilityFeatureVector(
            temporal_freshness=features.get("temporal_freshness", 0.5),
            source_credibility=features.get("source_credibility", 0.5),
            evidence_consistency=features.get("evidence_consistency", 0.5),
            evidence_sufficiency=features.get("evidence_sufficiency", 0.5)
        )
        
        return RRFEResult(features=vector, execution_metadata=metadata)
