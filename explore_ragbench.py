import sys
import json
import subprocess

try:
    from datasets import load_dataset
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
    from datasets import load_dataset

def main():
    print("Loading rungalileo/ragbench, subset hotpotqa...")
    try:
        ds = load_dataset("rungalileo/ragbench", "hotpotqa", split="train")
    except Exception as e:
        print(f"Error loading: {e}")
        return

    print("=== DATASET INFORMATION ===")
    print(f"Number of Samples: {len(ds)}")
    print(f"Dataset Features: {ds.features.keys()}")
    
    print("\n=== SAMPLE 0 ===")
    sample = ds[0]
    # Handle potentially non-serializable objects by doing a manual print or careful json dump
    print(json.dumps(sample, indent=2, default=str))
    
    # Calculate some stats for Task 6
    doc_lengths = []
    num_docs = []
    
    # Analyze a subset of 100 samples to keep it fast
    subset = ds.select(range(min(100, len(ds))))
    for item in subset:
        docs = item.get("documents", [])
        num_docs.append(len(docs))
        for d in docs:
            # RAGBench documents structure might vary, let's assume it's a list of strings or dicts
            if isinstance(d, dict):
                text = d.get("text", "") or d.get("content", "") or str(d)
            else:
                text = str(d)
            doc_lengths.append(len(text))
            
    print("\n=== DOCUMENT STATISTICS (Sample of 100) ===")
    print(f"Average documents per question: {sum(num_docs)/len(num_docs):.2f}")
    if doc_lengths:
        print(f"Average document length (chars): {sum(doc_lengths)/len(doc_lengths):.2f}")
        print(f"Max document length (chars): {max(doc_lengths)}")
        print(f"Min document length (chars): {min(doc_lengths)}")

if __name__ == "__main__":
    main()
