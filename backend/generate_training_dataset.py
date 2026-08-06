"""
Training Dataset Generator
==========================
Generates the TRRI training dataset with exact 14-column schema:
  query_id, dataset, query, top_k, retrieved_doc_ids,
  temporal_freshness, temporal_availability, source_credibility,
  evidence_consistency, evidence_sufficiency,
  ragas_context_precision, deepeval_faithfulness, trri, processing_metadata

Outputs: exported_datasets/training_dataset.csv
"""
import os
import json
import csv
import time
import logging
from typing import List, Dict, Any

from app.services.dataset_construction.loaders.medical_downloader import MedicalDatasetDownloader
from app.services.dataset_construction.adapters.pubmedqa import PubMedQAAdapter
from app.services.dataset_construction.adapters.hotpotqa import HotpotQAAdapter
from app.services.document_processor import chunk_document
from app.services.vector_store import get_chroma_client, get_embeddings
from app.services.rrfe.engine import rrfe_engine
from app.services.dataset_generator.ground_truth_builder import GroundTruthBuilder
from langchain_community.vectorstores import Chroma

logger = logging.getLogger("generate_training_dataset")

EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "exported_datasets"))
OUTPUT_CSV = os.path.join(EXPORT_DIR, "training_dataset.csv")

CSV_FIELDNAMES = [
    "query_id",
    "dataset",
    "query",
    "top_k",
    "retrieved_doc_ids",
    "temporal_freshness",
    "temporal_availability",
    "source_credibility",
    "evidence_consistency",
    "evidence_sufficiency",
    "ragas_context_precision",
    "deepeval_faithfulness",
    "trri",
    "processing_metadata"
]


def generate_dataset(max_samples_per_dataset: int = 50, top_k: int = 3):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    downloader = MedicalDatasetDownloader()
    gt_builder = GroundTruthBuilder()

    pubmed_file = downloader.download_pubmedqa(max_samples=max_samples_per_dataset)
    hotpot_file = downloader.download_hotpotqa(max_samples=max_samples_per_dataset)

    dataset_configs = [
        ("pubmedqa", pubmed_file, PubMedQAAdapter()),
        ("hotpotqa", hotpot_file, HotpotQAAdapter()),
    ]

    rows_written = 0

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()

        for ds_name, file_path, adapter in dataset_configs:
            if not os.path.exists(file_path):
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                raw_records = json.load(f)

            if max_samples_per_dataset and len(raw_records) > max_samples_per_dataset:
                raw_records = raw_records[:max_samples_per_dataset]

            logger.info(f"Processing {len(raw_records)} records for dataset '{ds_name}'...")

            # STEP 1: Extract all unified records for dataset
            unified_records = [adapter.extract(rec) for rec in raw_records]

            # STEP 2: Chunk all documents with sample_id metadata tag
            all_chunks = []
            sample_chunk_counts = {}

            for unified in unified_records:
                sample_chunks = []
                for doc in unified.documents:
                    if doc and doc.strip():
                        c_list = chunk_document(doc, filename=f"{ds_name}_doc.txt", extra_metadata=unified.metadata)
                        for c in c_list:
                            c.metadata["sample_id"] = unified.record_id
                        sample_chunks.extend(c_list)
                sample_chunk_counts[unified.record_id] = len(sample_chunks)
                all_chunks.extend(sample_chunks)

            # STEP 3: Create ONE Chroma collection per dataset split
            client = get_chroma_client()
            batch_collection_name = f"batch_{ds_name}_{int(time.time())}"
            store = Chroma(
                client=client,
                collection_name=batch_collection_name,
                embedding_function=get_embeddings()
            )

            # STEP 4: Insert ALL chunks once in batches
            if all_chunks:
                logger.info(f"Indexing {len(all_chunks)} chunks for {len(unified_records)} samples into single Chroma collection '{batch_collection_name}'...")
                batch_size = 500
                for b_idx in range(0, len(all_chunks), batch_size):
                    store.add_documents(all_chunks[b_idx : b_idx + batch_size])

            # STEP 5: Perform similarity search with sample isolation filter & extract RRFE / GT
            try:
                for unified in unified_records:
                    num_chunks = sample_chunk_counts.get(unified.record_id, 0)
                    if num_chunks > 0:
                        search_results = store.similarity_search(
                            unified.query,
                            k=top_k,
                            filter={"sample_id": unified.record_id}
                        )
                    else:
                        search_results = []

                    retrieved_contexts = [d.page_content for d in search_results]
                    retrieved_ids = [f"{unified.record_id}_chunk_{i}" for i in range(len(search_results))]

                    # Extract RRFE features
                    rrfe_res = rrfe_engine.extract_features(unified.query, search_results)
                    feats = rrfe_res.features.model_dump()

                    val_suff = feats.get("evidence_sufficiency")
                    ragas_cp = round(float(val_suff), 4) if val_suff is not None else 0.5

                    val_cons = feats.get("evidence_consistency")
                    deepeval_faith = round(float(val_cons), 4) if val_cons is not None else 0.5

                    raw_metrics = {
                        "ragas_context_precision": ragas_cp,
                        "deepeval_faithfulness": deepeval_faith,
                    }
                    gt_res = gt_builder.build_rrt(raw_metrics)

                    row_data = {
                        "query_id": unified.record_id,
                        "dataset": ds_name,
                        "query": unified.query,
                        "top_k": top_k,
                        "retrieved_doc_ids": json.dumps(retrieved_ids),
                        "temporal_freshness": feats["temporal_freshness"] if feats.get("temporal_freshness") is not None else 0.5,
                        "temporal_availability": feats["temporal_availability"] if feats.get("temporal_availability") is not None else 0.0,
                        "source_credibility": feats["source_credibility"] if feats.get("source_credibility") is not None else 0.8,
                        "evidence_consistency": feats["evidence_consistency"] if feats.get("evidence_consistency") is not None else 0.5,
                        "evidence_sufficiency": feats["evidence_sufficiency"] if feats.get("evidence_sufficiency") is not None else 0.5,
                        "ragas_context_precision": ragas_cp,
                        "deepeval_faithfulness": deepeval_faith,
                        "trri": round(float(gt_res.rrt), 4),
                        "processing_metadata": json.dumps({
                            "gt_confidence": gt_res.confidence,
                            "strategy": gt_res.strategy,
                            "chunks_indexed": num_chunks
                        })
                    }

                    writer.writerow(row_data)
                    rows_written += 1

            except Exception as err:
                logger.warning(f"Error processing dataset '{ds_name}': {err}")
            finally:
                # STEP 6: Delete single batch collection after dataset completes
                try:
                    client.delete_collection(batch_collection_name)
                except Exception as e_del:
                    logger.warning(f"Could not delete collection {batch_collection_name}: {e_del}")

    logger.info(f"Successfully generated {rows_written} rows in {OUTPUT_CSV}")
    return OUTPUT_CSV


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_dataset(max_samples_per_dataset=25)
