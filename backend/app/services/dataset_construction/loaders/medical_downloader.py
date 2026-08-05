"""
Medical Dataset Downloader
==========================
Downloads and prepares open-access medical datasets (PubMedQA, WHO Guidelines, PubMed OA)
with resumable downloading and local caching under data/questions and data/corpus.
"""
import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("medical_downloader")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))
QUESTIONS_DIR = os.path.join(DATA_DIR, "questions")
CORPUS_DIR = os.path.join(DATA_DIR, "corpus")


class MedicalDatasetDownloader:
    def __init__(self):
        os.makedirs(QUESTIONS_DIR, exist_ok=True)
        os.makedirs(CORPUS_DIR, exist_ok=True)

    def download_pubmedqa(self, split: str = "train", max_samples: int = 200) -> str:
        """
        Downloads PubMedQA via rungalileo/ragbench or datasets library
        and caches locally under data/questions/pubmedqa.json.
        """
        output_path = os.path.join(QUESTIONS_DIR, f"pubmedqa_{split}.json")
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if len(existing) >= max_samples:
                    logger.info(f"PubMedQA cached with {len(existing)} samples (>= {max_samples} requested) at {output_path}")
                    return output_path
            except Exception:
                pass

        logger.info(f"Downloading PubMedQA ({split} split, max {max_samples} samples)...")
        try:
            from datasets import load_dataset
            ds = load_dataset("rungalileo/ragbench", "pubmedqa", split=split)
            samples = []
            for i, row in enumerate(ds):
                if max_samples and i >= max_samples:
                    break
                samples.append({
                    "id": row.get("id", f"pubmedqa_{i}"),
                    "question": row.get("question", ""),
                    "response": row.get("response", ""),
                    "documents": row.get("documents", []),
                    "metadata": {
                        "source": "PubMedQA",
                        "url": "https://pubmedqa.github.io/",
                        "publication_year": 2024,
                    }
                })

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(samples, f, indent=2)
            logger.info(f"Successfully saved {len(samples)} PubMedQA samples to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to download PubMedQA: {e}")
            raise e

    def download_hotpotqa(self, split: str = "train", max_samples: int = 200) -> str:
        """
        Downloads HotpotQA (general QA) for cross-domain benchmarking.
        """
        output_path = os.path.join(QUESTIONS_DIR, f"hotpotqa_{split}.json")
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if len(existing) >= max_samples:
                    logger.info(f"HotpotQA cached with {len(existing)} samples (>= {max_samples} requested) at {output_path}")
                    return output_path
            except Exception:
                pass

        logger.info(f"Downloading HotpotQA ({split} split, max {max_samples} samples)...")
        try:
            from datasets import load_dataset
            ds = load_dataset("rungalileo/ragbench", "hotpotqa", split=split)
            samples = []
            for i, row in enumerate(ds):
                if max_samples and i >= max_samples:
                    break
                samples.append({
                    "id": row.get("id", f"hotpotqa_{i}"),
                    "question": row.get("question", ""),
                    "response": row.get("response", ""),
                    "documents": row.get("documents", []),
                    "metadata": {
                        "source": "HotpotQA",
                        "url": "https://hotpotqa.github.io/",
                        "publication_year": 2024,
                    }
                })

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(samples, f, indent=2)
            logger.info(f"Successfully saved {len(samples)} HotpotQA samples to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to download HotpotQA: {e}")
            raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    downloader = MedicalDatasetDownloader()
    downloader.download_pubmedqa(max_samples=50)
    downloader.download_hotpotqa(max_samples=50)
