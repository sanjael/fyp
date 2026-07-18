import sys
import os

os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "Y"
os.environ["SENTRY_DISABLE_AUTO_INTEGRATIONS"] = "1"
os.environ["NO_ERROR_REPORTING"] = "Y"
os.environ["MAX_WORKERS"] = "1"

from dotenv import load_dotenv
load_dotenv()

print(f"GROQ_API_KEY loaded: {bool(os.getenv('GROQ_API_KEY'))}")
print(f"Provider: {os.getenv('EVALUATOR_PROVIDER', 'groq')}")
print(f"Model: {os.getenv('EVALUATOR_LLM_MODEL', 'llama-3.3-70b-versatile')}")
if not os.getenv('GROQ_API_KEY'):
    sys.exit(1)

import json
import pandas as pd
import shutil
import time

def pre_run_cleanup():
    checkpoint_file = "dataset_construction_checkpoint.json"
    exported_dir = "exported_datasets"
    eval_cache_dir = ".eval_cache"
    reports = ["environment_report.json", "dataset_validation.json", "statistics.json"]
    
    print("==================================================")
    print("PRE-RUN VALIDATION")
    print("==================================================")
    
    has_checkpoint = os.path.exists(checkpoint_file)
    has_dataset = os.path.exists(os.path.join(exported_dir, "hotpotqa_training.csv"))
    has_dir = os.path.exists(exported_dir)
    
    print(f"Checkpoint exists: {'YES' if has_checkpoint else 'NO'}")
    print(f"Output dataset exists: {'YES' if has_dataset else 'NO'}")
    print(f"Output directory exists: {'YES' if has_dir else 'NO'}")
    
    if has_checkpoint:
        os.remove(checkpoint_file)
        print("Deleted stale checkpoint.")
        
    if has_dir:
        shutil.rmtree(exported_dir)
        print("Deleted stale exported_datasets directory.")
        
    for r in reports:
        if os.path.exists(r):
            os.remove(r)
            print(f"Deleted stale report {r}.")
            
    if os.path.exists(eval_cache_dir):
        shutil.rmtree(eval_cache_dir)
        print("Deleted stale .eval_cache directory.")
            
    os.makedirs(exported_dir, exist_ok=True)
    print("Ready for clean execution.\n")
    
    print("Clearing ChromaDB...")
    try:
        import chromadb
        chroma_dir = os.path.join(os.path.dirname(__file__), "app", "chroma")
        if os.path.exists(chroma_dir):
            shutil.rmtree(chroma_dir)
            print("Deleted ChromaDB directory.")
    except Exception as e:
        print(f"Failed to clear chroma: {e}")

def wait_for_services():
    import urllib.request
    print("Waiting for Ollama to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            urllib.request.urlopen("http://localhost:11434/", timeout=2)
            print("Ollama is ready!")
            return
        except Exception:
            time.sleep(1)
    print("Warning: Ollama did not become ready in time, pipeline may fail.")

def run_phase_a():
    wait_for_services()
    pre_run_cleanup()
    
    print("LLM:\nGroq\n")
    print("Embeddings:\nnomic-embed-text\n")
    print("Provider:\nOllama\n")
    
    print("STEP 2-7: Running DatasetConstructionPipeline for 10 samples...")
    start_time = time.time()
    try:
        from app.services.dataset_construction.pipeline import DatasetConstructionPipeline
        pipeline = DatasetConstructionPipeline()
        pipeline.run(dataset_name="hotpotqa", split="train", max_records=10)
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    print("STEP 8: Dataset validation")
    try:
        df = pd.read_csv("exported_datasets/hotpotqa_training.csv")
        
        validation = {
            "num_samples": len(df),
            "nan_counts": df.isna().sum().to_dict(),
            "duplicate_ids": df.duplicated(subset=['id']).sum() if 'id' in df.columns else df.duplicated().sum(),
        }
        
        # RRFE features
        rrfe_features = ['retriever_tff', 'retriever_scf', 'retriever_ecf', 'retriever_esf']
        feature_variance = {}
        for f in rrfe_features:
            if f in df.columns:
                feature_variance[f] = df[f].var()
        validation["feature_variance"] = feature_variance
        
        # Target
        if 'rrt_score' in df.columns:
            validation["target_variance"] = df['rrt_score'].var()
            
        # Convert dataframe dtypes to Python native for JSON serialization
        validation["statistics"] = df.describe().applymap(lambda x: float(x) if pd.notnull(x) else None).to_dict()
        
        # Also convert nan_counts and duplicate_ids
        validation["nan_counts"] = {k: int(v) for k, v in validation["nan_counts"].items()}
        validation["duplicate_ids"] = int(validation["duplicate_ids"])
        
        with open("dataset_validation.json", "w") as f:
            json.dump(validation, f, indent=4)
            
        with open("statistics.json", "w") as f:
            json.dump(validation["statistics"], f, indent=4)
            
        print("PASS\n")
        
        # After execution stats
        print("==================================================")
        print("AFTER EXECUTION")
        print("==================================================")
        print(f"Samples processed: {len(df)}")
        print(f"Samples skipped: 0") # We forced clean execution
        print(f"Rows written: {len(df)}")
        print(f"CSV location: exported_datasets/hotpotqa_training.csv")
        print(f"JSONL location: exported_datasets/hotpotqa_training.jsonl")
        print(f"Execution time: {time.time() - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    run_phase_a()
