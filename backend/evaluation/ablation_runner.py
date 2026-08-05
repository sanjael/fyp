"""
RAGGuard-TR Feature Ablation Runner
===================================
Executes 5 leave-one-out feature ablation experiments to measure the relative
predictive contribution of each RRFE feature for TRRI modeling.

Usage:
    cd e:/fyp/backend
    python -m evaluation.ablation_runner --dataset exported_datasets/hotpotqa_training.csv
"""
import argparse
import json
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    from sklearn.ensemble import RandomForestRegressor

ALL_FEATURES = [
    "temporal_freshness",
    "temporal_availability",
    "source_credibility",
    "evidence_consistency",
    "evidence_sufficiency",
]


def run_ablation(dataset_path: str, out_dir: str = "evaluation/results/ablation"):
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset {dataset_path} not found.")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    target_col = "trri" if "trri" in df.columns else ("rrt" if "rrt" in df.columns else None)
    if not target_col:
        print("Error: Neither 'trri' nor 'rrt' target column found.")
        sys.exit(1)

    if "rrfe_features" in df.columns and not all(f in df.columns for f in ALL_FEATURES):
        df["parsed_features"] = df["rrfe_features"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, dict) else {})
        )
        for feat in ALL_FEATURES:
            df[feat] = df["parsed_features"].apply(
                lambda x: x.get(feat, 0.5) if isinstance(x, dict) else 0.5
            )

    y = df[target_col].values
    valid_idx = ~np.isnan(y)
    y = y[valid_idx]

    results = []

    # 1. Full Model Baseline
    X_full = df[ALL_FEATURES].fillna(0.5).values[valid_idx]
    X_tr, X_te, y_tr, y_te = train_test_split(X_full, y, test_size=0.2, random_state=42)

    if XGB_AVAILABLE:
        model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)

    model.fit(X_tr, y_tr)
    preds = model.predict(X_te)
    base_r2 = float(r2_score(y_te, preds))
    base_rmse = float(np.sqrt(mean_squared_error(y_te, preds)))
    base_mae = float(mean_absolute_error(y_te, preds))

    results.append({
        "configuration": "Full Model (5 Features)",
        "omitted_feature": "None",
        "r2_score": round(base_r2, 4),
        "rmse": round(base_rmse, 4),
        "mae": round(base_mae, 4),
        "r2_drop": 0.0,
        "rmse_increase": 0.0,
    })

    print(f"Full Model Baseline -> R2: {base_r2:.4f}, RMSE: {base_rmse:.4f}")

    # 2. Leave-One-Out Ablations
    for omitted in ALL_FEATURES:
        sub_features = [f for f in ALL_FEATURES if f != omitted]
        X_sub = df[sub_features].fillna(0.5).values[valid_idx]
        X_tr, X_te, y_tr, y_te = train_test_split(X_sub, y, test_size=0.2, random_state=42)

        if XGB_AVAILABLE:
            m = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
        else:
            m = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)

        m.fit(X_tr, y_tr)
        sub_preds = m.predict(X_te)
        r2 = float(r2_score(y_te, sub_preds))
        rmse = float(np.sqrt(mean_squared_error(y_te, sub_preds)))
        mae = float(mean_absolute_error(y_te, sub_preds))

        r2_drop = round(base_r2 - r2, 4)
        rmse_inc = round(rmse - base_rmse, 4)

        results.append({
            "configuration": f"Omit {omitted}",
            "omitted_feature": omitted,
            "r2_score": round(r2, 4),
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "r2_drop": r2_drop,
            "rmse_increase": rmse_inc,
        })
        print(f"Omit {omitted:<22} -> R2: {r2:.4f} (Drop: {r2_drop:+.4f}), RMSE: {rmse:.4f}")

    res_df = pd.DataFrame(results)
    csv_path = os.path.join(out_dir, "ablation_results.csv")
    res_df.to_csv(csv_path, index=False)
    print(f"\nAblation results saved to {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAGGuard-TR Feature Ablation Runner")
    parser.add_argument("--dataset", type=str, default="exported_datasets/hotpotqa_training.csv", help="Path to training dataset CSV")
    parser.add_argument("--out_dir", type=str, default="evaluation/results/ablation", help="Output directory")
    args = parser.parse_args()
    run_ablation(args.dataset, args.out_dir)
