"""
RAGGuard-TR End-to-End Dataset & ML Pipeline Orchestrator
=========================================================
Single-command pipeline execution:

    python run_dataset_pipeline.py

Execution Steps:
  1. Download healthcare & general QA datasets (PubMedQA, HotpotQA)
  2. Prepare corpus and metadata
  3. Index documents into ChromaDB
  4. Generate training dataset (exported_datasets/training_dataset.csv)
  5. Validate dataset & write report (exported_datasets/dataset_report.md)
  6. Train XGBoost predictor with 5-Fold Cross Validation
  7. Generate residual, calibration, and IEEE publication figures
  8. Save trained model artifacts (artifacts/latest_model.pkl)
"""
import os
import sys
import logging
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.dataset_construction.loaders.medical_downloader import MedicalDatasetDownloader
from generate_training_dataset import generate_dataset
from generate_dataset_report import generate_report
from app.services.predictor.train import Trainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline_orchestrator")


def run_full_pipeline(max_samples: int = 50):
    t0 = time.time()
    logger.info("==========================================================")
    logger.info("STARTING RAGGUARD-TR END-TO-END DATASET & ML PIPELINE")
    logger.info("==========================================================")

    # 1. Download Datasets
    logger.info("\n--- Step 1: Downloading Datasets ---")
    downloader = MedicalDatasetDownloader()
    p_pubmed = downloader.download_pubmedqa(max_samples=max_samples)
    p_hotpot = downloader.download_hotpotqa(max_samples=max_samples)
    logger.info(f"Downloaded datasets: {p_pubmed}, {p_hotpot}")

    # 2 & 3 & 4. Corpus Preparation, ChromaDB, & Training Dataset Generation
    logger.info("\n--- Steps 2, 3 & 4: Generating Training Dataset (14-column schema) ---")
    csv_path = generate_dataset(max_samples_per_dataset=max_samples)
    logger.info(f"Training dataset generated at: {csv_path}")

    # 5. Dataset Validation & Report
    logger.info("\n--- Step 5: Validating Dataset & Generating Report ---")
    report_path = generate_report(csv_path=csv_path)
    logger.info(f"Validation report generated at: {report_path}")

    # 6, 7 & 8. Model Training, Plots, & Model Saving
    logger.info("\n--- Steps 6, 7 & 8: Training XGBoost Predictor & Saving Artifacts ---")
    trainer = Trainer()
    trainer.train(dataset_path=csv_path, version="v1.0.latest")

    total_min = (time.time() - t0) / 60.0
    logger.info("==========================================================")
    logger.info(f"PIPELINE COMPLETED SUCCESSFULLY IN {total_min:.2f} MINUTES")
    logger.info("Artifacts generated:")
    logger.info("  - Training Dataset: exported_datasets/training_dataset.csv")
    logger.info("  - Validation Report: exported_datasets/dataset_report.md")
    logger.info("  - Trained Model: app/services/predictor/artifacts/latest_model.pkl")
    logger.info("  - Metrics & Plots: app/services/predictor/artifacts/latest/")
    logger.info("==========================================================")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run RAGGuard-TR End-to-End Dataset & ML Pipeline")
    parser.add_argument("--samples", type=int, default=25, help="Max samples per dataset split for generation")
    args = parser.parse_args()

    run_full_pipeline(max_samples=args.samples)
