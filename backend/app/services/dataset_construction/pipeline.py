import time
import concurrent.futures
from typing import Dict, Any

from .config import config
from .logger import get_logger
from .checkpointing import CheckpointManager
from .models import FinalDatasetRow
from .loaders.hf_loader import HuggingFaceLoader
from .adapters.hotpotqa import HotpotQAAdapter
# from .adapters.pubmedqa import PubMedQAAdapter
# from .adapters.techqa import TechQAAdapter
from .processor.document_indexer import RAGProcessor
from .evaluators.ragas_wrapper import RagasWrapper
from .evaluators.deepeval_wrapper import DeepEvalWrapper
from .evaluators.metric_calibration import MetricCalibrator
from .reliability.estimator import EvaluatorReliabilityEstimator
from .exporters.multi_exporter import MultiExporter
from .exporters.report_generator import DatasetStatisticsGenerator

from ..rrfe.engine import rrfe_engine
from ..dataset_generator.ground_truth_builder import GroundTruthBuilder
import json

PROFILING_TRACES = []
REQUEST_TRACES = []

class DatasetConstructionPipeline:
    def __init__(self):
        self.logger = get_logger("DatasetConstruction")
        self.checkpoint_manager = CheckpointManager()
        self.loader = HuggingFaceLoader()
        
        # Determine adapter dynamically based on dataset name
        self.adapters = {
            "hotpotqa": HotpotQAAdapter(),
            # "pubmedqa": PubMedQAAdapter(),
            # "techqa": TechQAAdapter()
        }
        
        self.processor = RAGProcessor()
        self.ragas = RagasWrapper()
        self.deepeval = DeepEvalWrapper()
        self.calibrator = MetricCalibrator()
        self.reliability_estimator = EvaluatorReliabilityEstimator()
        self.gt_builder = GroundTruthBuilder()
        self.exporter = MultiExporter(config.EXPORT_DIR)
        self.stats = DatasetStatisticsGenerator(config.EXPORT_DIR)

    def _process_single_record(self, raw_record: Dict[str, Any], dataset_name: str, adapter) -> bool:
        start_time = time.time()
        
        # 1. Extract
        load_start = time.time()
        unified = adapter.extract(raw_record)
        load_time = (time.time() - load_start) * 1000
        
        if self.checkpoint_manager.is_processed(unified.record_id):
            return True
            
        try:
            from ...core.evaluator_provider.base import current_sample_id
            token = current_sample_id.set(unified.record_id)
            
            # We must reset metrics at the start of a sample to only count this sample
            from ...core.evaluator_provider.factory import get_evaluator_provider
            provider = get_evaluator_provider()
            provider.get_and_reset_metrics()
            
            self.logger.info(f"Processing record: {unified.record_id}")
            
            # 2. Process & Retrieve
            chunk_start = time.time()
            total_chunks = 0
            from ..document_processor import chunk_document
            for doc in unified.documents:
                total_chunks += len(chunk_document(doc, filename='dummy.txt'))
            chunk_time = (time.time() - chunk_start) * 1000
            
            from ..embedding_engine import get_vector_store
            vector_store = get_vector_store()
            chroma_count_before = vector_store._collection.count()
            
            embed_start = time.time()
            self.processor.index_documents(unified.documents)
            embed_time = (time.time() - embed_start) * 1000
            
            chroma_count_after = vector_store._collection.count()
            chunks_inserted = chroma_count_after - chroma_count_before
            
            retrieval_start = time.time()
            retrieved_docs = self.processor.retrieve(unified.query, top_k=3)
            retrieval_time = (time.time() - retrieval_start) * 1000
            retrieved_ids = [doc.metadata.get("chunk_id", "unknown") for doc in retrieved_docs]
            
            from ..embedding_engine import search_documents
            results_with_scores = search_documents(unified.query, k=3)
            retrieved_count = len(results_with_scores)
            for i, (doc, score) in enumerate(results_with_scores):
                print(f" Chunk {i+1} ID: {doc.metadata.get('chunk_id', 'unknown')}")
                print(f" Chunk {i+1} Score: {score}")
                print(f" Chunk {i+1} Text snippet: {doc.page_content[:300]}")
            rrfe_start = time.time()
            rrfe_result = rrfe_engine.extract_features(unified.query, retrieved_docs)
            rrfe_features = rrfe_result.features.model_dump()
            rrfe_time = (time.time() - rrfe_start) * 1000
            
            # 4. Evaluate (Mock parallel execution)
            ragas_start = time.time()
            ragas_metrics = self.ragas.compute_metrics(unified.query, unified.ground_truth_answer, retrieved_docs)
            ragas_time = (time.time() - ragas_start) * 1000
            
            deepeval_start = time.time()
            deepeval_metrics = self.deepeval.compute_metrics(unified.query, unified.ground_truth_answer, retrieved_docs)
            deepeval_time = (time.time() - deepeval_start) * 1000
            
            raw_metrics = {**ragas_metrics, **deepeval_metrics}
            eval_time = ragas_time + deepeval_time
            
            # 5. Calibrate
            calibrated = self.calibrator.calibrate(raw_metrics)
            
            # 6. Reliability Estimator
            reliability_weights = self.reliability_estimator.estimate_reliability(calibrated)
            
            # 7. Ground Truth Builder
            # We construct a weighted metrics dictionary for the GT builder
            weighted_metrics = {}
            for k, v in calibrated.items():
                framework = "ragas" if "ragas" in k else "deepeval"
                weighted_metrics[k] = v * reliability_weights.get(framework, 1.0)
                
            rrt_start = time.time()
            gt_result = self.gt_builder.build_rrt(weighted_metrics)
            rrt_time = (time.time() - rrt_start) * 1000
            
            total_time = (time.time() - start_time) * 1000
            
            # 8. Export
            export_start = time.time()
            # Collect metrics from evaluator provider
            try:
                from ...core.config import global_config
                metrics_obj = provider.get_and_reset_metrics()
                provider_metrics = metrics_obj.model_dump()
                provider_name = provider.model_name
                evaluator_provider = global_config.EVALUATOR_PROVIDER
            except Exception as e:
                self.logger.error(f"Provider import failed: {e}")
                metrics_obj = None
                provider_metrics = {}
                provider_name = "unknown"
                evaluator_provider = "unknown"
                
            row = FinalDatasetRow(
                session_id=unified.record_id,
                dataset_name=dataset_name,
                query=unified.query,
                ground_truth_answer=unified.ground_truth_answer,
                retrieved_chunk_ids=retrieved_ids,
                rrfe_features=rrfe_features,
                raw_metrics=raw_metrics,
                calibrated_metrics=calibrated,
                evaluator_reliability=reliability_weights,
                rrt=gt_result.rrt,
                processing_metadata={
                    "rrfe_time_ms": rrfe_time,
                    "eval_time_ms": eval_time,
                    "total_time_ms": total_time,
                    "experiment_config": {
                        "evaluator_provider": evaluator_provider,
                        "evaluator_model": provider_name
                    },
                    "llm_metrics": provider_metrics
                }
            )
            
            self.exporter.export(row, dataset_name)
            export_time = (time.time() - export_start) * 1000
            
            self.checkpoint_manager.mark_processed(unified.record_id)
            self.stats.add_sample(gt_result.rrt, total_time, has_failure=False)
            
            # Build and print profile
            if metrics_obj:
                profile = {
                    "Sample ID": unified.record_id,
                    "Question": unified.query,
                    "Retrieved Chunks": retrieved_count,
                    "Chunks Indexed": chunks_inserted,
                    "Total Documents": len(unified.documents),
                    "Groq Requests (Retries + Unique)": metrics_obj.total_requests,
                    "Unique Requests": metrics_obj.unique_requests,
                    "Prompt Tokens": metrics_obj.prompt_tokens,
                    "Completion Tokens": metrics_obj.completion_tokens,
                    "Total Tokens": metrics_obj.prompt_tokens + metrics_obj.completion_tokens,
                    "Retries": metrics_obj.retry_count,
                    "429 Count": metrics_obj.http_429_count,
                    "Groq Time": metrics_obj.latency_ms / 1000.0,
                    "Rate Limit Wait Time": metrics_obj.rate_limit_wait_time_ms / 1000.0,
                    "RAGAS Time": ragas_time / 1000.0,
                    "DeepEval Time": deepeval_time / 1000.0,
                    "Loading Time": load_time / 1000.0,
                    "Chunking Time": chunk_time / 1000.0,
                    "Embedding Time": embed_time / 1000.0,
                    "Retrieval Time": retrieval_time / 1000.0,
                    "RRFE Time": rrfe_time / 1000.0,
                    "RRT Time": rrt_time / 1000.0,
                    "Export Time": export_time / 1000.0,
                    "Total Pipeline Time": total_time / 1000.0,
                    "Cache Hits": metrics_obj.cache_hit_count,
                    "Cache Misses": metrics_obj.cache_miss_count,
                    "Average Cache Lookup Time": metrics_obj.cache_lookup_time_ms / (metrics_obj.cache_hit_count + metrics_obj.cache_miss_count) if (metrics_obj.cache_hit_count + metrics_obj.cache_miss_count) > 0 else 0,
                    "Groq Model": provider_name
                }
                PROFILING_TRACES.append(profile)
                
                print("\n====================================================")
                print(f"Sample {len(PROFILING_TRACES)}")
                print(f"Sample ID: {profile['Sample ID']}")
                print(f"Question: {profile['Question']}")
                print(f"Retrieved Chunks: {profile['Retrieved Chunks']}")
                print(f"Unique API Requests: {profile['Unique Requests']}")
                print(f"Total Attempted Requests (w/ Retries): {profile['Groq Requests (Retries + Unique)']}")
                print(f"Prompt Tokens: {profile['Prompt Tokens']:,}")
                print(f"Completion Tokens: {profile['Completion Tokens']:,}")
                print(f"Total Tokens: {profile['Total Tokens']:,}")
                print(f"Retries: {profile['Retries']}")
                print(f"HTTP 429: {profile['429 Count']}")
                print(f"Rate Limiter Wait Time: {profile['Rate Limit Wait Time']:.2f} s")
                print(f"Groq Inference Time: {profile['Groq Time']:.2f} s")
                print(f"RAGAS Time: {profile['RAGAS Time']:.2f} s")
                print(f"DeepEval Time: {profile['DeepEval Time']:.2f} s")
                print(f"Total Pipeline Time: {profile['Total Pipeline Time']:.2f} s")
                print("====================================================")
            
            self.logger.info(f"Successfully processed record {unified.record_id} with RRT {gt_result.rrt:.3f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process record {unified.record_id}: {e}")
            self.stats.add_sample(0.0, (time.time() - start_time) * 1000, has_failure=True)
            return False
        finally:
            current_sample_id.reset(token)

    def _wait_for_chroma(self):
        self.logger.info("Verifying ChromaDB and Embedding Engine initialization...")
        max_retries = 30
        for i in range(max_retries):
            try:
                # Attempt to embed and insert a dummy chunk to prove readiness
                from ..embedding_engine import add_documents_to_chroma, search_documents
                from langchain_core.documents import Document
                dummy_doc = [Document(page_content="healthcheck", metadata={"chunk_id": "healthcheck"})]
                add_documents_to_chroma(dummy_doc)
                # If we get here, insertion and embeddings work.
                self.logger.info("ChromaDB and Embedding Engine are fully initialized.")
                return
            except Exception as e:
                self.logger.warning(f"Waiting for ChromaDB/Ollama... ({e})")
                time.sleep(2)
        raise RuntimeError("ChromaDB or Embedding Engine failed to initialize in time.")

    def run(self, dataset_name: str, split: str = "train", max_records: int = 100):
        self._wait_for_chroma()
        self.logger.info(f"Starting pipeline for {dataset_name} ({split})")
        adapter = self.adapters.get(dataset_name)
        if not adapter:
            raise ValueError(f"No adapter found for dataset: {dataset_name}")
            
        records = self.loader.load_split(dataset_name, split, streaming=False)
        
        # Process in parallel
        processed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = []
            for record in records:
                if processed_count >= max_records:
                    break
                futures.append(executor.submit(self._process_single_record, record, dataset_name, adapter))
                processed_count += 1
                
            concurrent.futures.wait(futures)
            
        self.logger.info(f"Completed pipeline run. Generating reports...")
        self.stats.generate_report(dataset_name)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name (e.g., hotpot_qa)")
    parser.add_argument("--split", type=str, default="train")
    parser.add_argument("--max_records", type=int, default=100)
    args = parser.parse_args()
    
    pipeline = DatasetConstructionPipeline()
    pipeline.run(args.dataset, args.split, args.max_records)
