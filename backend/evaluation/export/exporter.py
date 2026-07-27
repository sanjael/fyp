"""
Experiment log exporter.

Writes two files per experiment run:
  - experiment_log.csv   — flat per-sample table (all fields)
  - experiment_log.json  — structured per-sample records (full fidelity)
"""
import csv
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger("eval.export")


def _safe_path(base_dir: str, filename: str) -> str:
    """Resolve path and assert it stays within base_dir (prevents path traversal)."""
    resolved = os.path.realpath(os.path.join(base_dir, os.path.basename(filename)))
    if not resolved.startswith(os.path.realpath(base_dir)):
        raise ValueError(f"Path traversal detected: {filename}")
    return resolved


def _flatten(record: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten nested dicts one level deep for CSV compatibility."""
    flat = {}
    for k, v in record.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat[f"{k}__{sub_k}"] = sub_v
        elif isinstance(v, list):
            flat[k] = json.dumps(v)
        else:
            flat[k] = v
    return flat


class ExperimentExporter:
    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

    def export(self, records: List[Dict[str, Any]], run_name: str) -> None:
        """
        records: list of merged dicts (PipelineResult + MetricResult fields).
        run_name: used as filename prefix.
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        # Sanitise run_name to prevent path traversal via the prefix
        safe_run_name = os.path.basename(run_name).replace("..", "")
        base = f"{safe_run_name}_{ts}"

        # JSON — full fidelity
        json_path = _safe_path(self.out_dir, f"{base}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, default=str)
        logger.info(f"Exported JSON: {json_path}")

        # CSV — flat
        if not records:
            return
        flat_records = [_flatten(r) for r in records]
        all_keys = list(dict.fromkeys(k for r in flat_records for k in r.keys()))
        csv_path = _safe_path(self.out_dir, f"{base}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(flat_records)
        logger.info(f"Exported CSV: {csv_path}")
