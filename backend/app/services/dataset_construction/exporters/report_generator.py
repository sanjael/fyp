import os
import json
from typing import List, Dict
import numpy as np

class DatasetStatisticsGenerator:
    def __init__(self, export_dir: str):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        self.rrt_scores = []
        self.latencies = []
        self.failed_evaluations = 0
        self.total_processed = 0

    def add_sample(self, rrt: float, latency_ms: float, has_failure: bool):
        self.rrt_scores.append(rrt)
        self.latencies.append(latency_ms)
        self.total_processed += 1
        if has_failure:
            self.failed_evaluations += 1

    def generate_report(self, dataset_name: str):
        report = {
            "dataset": dataset_name,
            "total_processed": self.total_processed,
            "failed_evaluations": self.failed_evaluations,
            "failure_rate": round(self.failed_evaluations / max(1, self.total_processed), 4),
            "mean_rrt": round(float(np.mean(self.rrt_scores)), 4) if self.rrt_scores else 0.0,
            "median_rrt": round(float(np.median(self.rrt_scores)), 4) if self.rrt_scores else 0.0,
            "std_rrt": round(float(np.std(self.rrt_scores)), 4) if self.rrt_scores else 0.0,
            "mean_latency_ms": round(float(np.mean(self.latencies)), 2) if self.latencies else 0.0
        }
        
        report_path = os.path.join(self.export_dir, f"{dataset_name}_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4)
            
        return report
