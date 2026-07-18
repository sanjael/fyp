from typing import List, Optional
from langchain_core.documents import Document
from ..rrfe.models import ReliabilityFeatureVector
from .models import DatasetSample
from .sample_builder import SampleBuilder
from .evaluator_runner import EvaluatorRunner
from .exporters.csv_exporter import CSVExporter

class DatasetEngine:
    def __init__(self):
        self.sample_builder = SampleBuilder()
        self.evaluator_runner = EvaluatorRunner()
        self.exporter = CSVExporter()
        
    def process_session(self, query: str, docs: List[Document], rrfe_vector: ReliabilityFeatureVector) -> DatasetSample:
        """
        Process a single retrieval session: runs evaluators and builds a dataset sample.
        """
        # 1. Run all independent evaluators to get raw metrics
        raw_metrics = self.evaluator_runner.run_all(query, docs)
        
        # 2. Build the structured DatasetSample
        sample = self.sample_builder.build(query, docs, rrfe_vector, raw_metrics)
        
        return sample
        
    def export(self, samples: List[DatasetSample], filepath: str = "dataset.csv") -> bool:
        """
        Export a batch of samples to disk.
        """
        return self.exporter.export(samples, filepath)

# Singleton instance
dataset_engine = DatasetEngine()
