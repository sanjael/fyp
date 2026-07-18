from pydantic_settings import BaseSettings
from typing import List
import os

class DatasetConstructionConfig(BaseSettings):
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = int(os.environ.get("MAX_WORKERS", os.cpu_count() or 4))
    CHECKPOINT_FILE: str = "dataset_construction_checkpoint.json"
    EXPORT_DIR: str = "exported_datasets"
    SUPPORTED_EVALUATORS: List[str] = ["ragas_context_precision", "ragas_faithfulness", "deepeval_faithfulness", "deepeval_answer_relevancy"]
    
config = DatasetConstructionConfig()
