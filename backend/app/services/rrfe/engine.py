from typing import List
from langchain_core.documents import Document
from .registry import FeatureRegistry
from .models import RRFEResult

class RRFEEngine:
    def __init__(self):
        self.registry = FeatureRegistry()
        
    def extract_features(self, query: str, docs: List[Document]) -> RRFEResult:
        """
        Main entrypoint for RRFE feature extraction.
        Takes the user query and retrieved documents, executes all registered plugins,
        and returns the feature vector and execution metadata.
        """
        return self.registry.execute_all(query, docs)

# Singleton instance for easy import
rrfe_engine = RRFEEngine()
