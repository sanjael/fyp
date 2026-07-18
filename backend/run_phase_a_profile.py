import sys
import os

os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "Y"
os.environ["SENTRY_DISABLE_AUTO_INTEGRATIONS"] = "1"
os.environ["NO_ERROR_REPORTING"] = "Y"
os.environ["MAX_WORKERS"] = "1"

from dotenv import load_dotenv
load_dotenv()

import json
import csv
from app.core.config import global_config
import time

def generate_profiling_reports(PROFILING_TRACES, REQUEST_TRACES):
    if not REQUEST_TRACES:
        print("No traces found to profile.")
        return

    # 1. groq_request_trace.csv (Detailed)
    keys = REQUEST_TRACES[0].keys()
    with open("groq_request_trace.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(REQUEST_TRACES)
        
    samples_processed = len(PROFILING_TRACES)
    total_groq_reqs = sum(t["Groq Requests (Retries + Unique)"] for t in PROFILING_TRACES)
    total_unique_reqs = sum(t["Unique Requests"] for t in PROFILING_TRACES)
    total_wait_time = sum(t["Rate Limit Wait Time"] for t in PROFILING_TRACES)
    
    avg_reqs = total_groq_reqs / samples_processed
    avg_unique_reqs = total_unique_reqs / samples_processed
    avg_wait = total_wait_time / samples_processed
    
    groq_data = {
        "total_requests_including_retries": total_groq_reqs,
        "total_unique_requests": total_unique_reqs,
        "average_unique_requests_per_sample": avg_unique_reqs,
        "average_requests_per_sample_including_retries": avg_reqs,
        "average_rate_limit_wait_s": avg_wait,
    }
    with open("groq_summary_stats.json", "w") as f:
        json.dump(groq_data, f, indent=4)

    # 2. groq_request_summary.csv (Grouped)
    grouped = {}
    for r in REQUEST_TRACES:
        k = (r["Framework"], r["Metric"], r["Prompt Type"])
        if k not in grouped:
            grouped[k] = {"Count": 0, "Total Tokens": 0, "Total Latency": 0.0, "Retries": 0, "429s": 0}
        grouped[k]["Count"] += 1
        grouped[k]["Total Tokens"] += r["Total Tokens"]
        grouped[k]["Total Latency"] += r["Latency"]
        grouped[k]["Retries"] += r["Retries"]
        if r["HTTP Status"] == 429:
            grouped[k]["429s"] += 1
            
    with open("groq_request_summary.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Framework", "Metric", "Prompt Type", "Count", "Average Tokens", "Average Latency", "Retries", "429s"])
        for k, v in grouped.items():
            count = v["Count"]
            writer.writerow([
                k[0], k[1], k[2], 
                count, 
                round(v["Total Tokens"] / count, 1) if count else 0,
                round(v["Total Latency"] / count, 2) if count else 0,
                v["Retries"],
                v["429s"]
            ])

    # 3. sample_request_breakdown.csv
    # Sample | Total Requests | Faithfulness | Context Precision | Answer Relevancy | DeepEval | Total Tokens | Total Time
    sample_stats = {}
    for r in REQUEST_TRACES:
        sid = r["Sample ID"]
        if sid not in sample_stats:
            sample_stats[sid] = {
                "Total Requests": 0,
                "Faithfulness": 0,
                "Context Precision": 0,
                "Answer Relevancy": 0,
                "DeepEval": 0,
                "Total Tokens": 0,
                "Total Time": 0.0
            }
        
        sample_stats[sid]["Total Requests"] += 1
        sample_stats[sid]["Total Tokens"] += r["Total Tokens"]
        sample_stats[sid]["Total Time"] += r["Latency"]
        
        # Categorize
        if r["Framework"] == "DeepEval":
            sample_stats[sid]["DeepEval"] += 1
        elif r["Metric"] == "Faithfulness":
            sample_stats[sid]["Faithfulness"] += 1
        elif r["Metric"] == "Context Precision":
            sample_stats[sid]["Context Precision"] += 1
        elif r["Metric"] == "Answer Relevancy":
            sample_stats[sid]["Answer Relevancy"] += 1

    with open("sample_request_breakdown.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Sample", "Total Requests", "Faithfulness", "Context Precision", "Answer Relevancy", "DeepEval", "Total Tokens", "Total Time"])
        for sid, v in sample_stats.items():
            writer.writerow([
                sid,
                v["Total Requests"],
                v["Faithfulness"],
                v["Context Precision"],
                v["Answer Relevancy"],
                v["DeepEval"],
                v["Total Tokens"],
                f"{v['Total Time']:.1f} s"
            ])
            
    print("Generated groq_request_trace.csv, groq_request_summary.csv, and sample_request_breakdown.csv")


def run_profiler():
    import run_phase_a
    run_phase_a.pre_run_cleanup()
    
    from app.services.dataset_construction.pipeline import DatasetConstructionPipeline, PROFILING_TRACES, REQUEST_TRACES
    
    pipeline = DatasetConstructionPipeline()
    try:
        pipeline.run(dataset_name="hotpotqa", max_records=10)
    finally:
        generate_profiling_reports(PROFILING_TRACES, REQUEST_TRACES)

if __name__ == "__main__":
    global_config.MAX_WORKERS = 1
    run_profiler()

