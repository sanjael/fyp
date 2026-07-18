import pandas as pd
import json
import numpy as np

df = pd.read_csv('exported_datasets/hotpotqa_training.csv')

def parse_json(s):
    try:
        return json.loads(s.replace("'", '"'))
    except Exception:
        return {}

print("\n=== Metadata ===")
meta = [parse_json(x).get('experiment_config', {}) for x in df['processing_metadata']]
mdf = pd.DataFrame(meta)
if not mdf.empty and 'evaluator_provider' in mdf.columns:
    print(mdf[['evaluator_provider', 'evaluator_model']].value_counts())
else:
    print("No experiment_config metadata found")

print("\n=== RRFE Variances ===")
rrfe = [parse_json(x) for x in df['rrfe_features']]
rdf = pd.DataFrame(rrfe)
if not rdf.empty:
    print(rdf.var())
else:
    print("No RRFE data")

print("\n=== RRT Variance ===")
if 'rrt' in df.columns:
    print(df['rrt'].describe())
    print(f"Variance: {df['rrt'].var()}")
else:
    print("No RRT data")
