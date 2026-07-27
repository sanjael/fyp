import os
import json
import uuid
import datetime
import pandas as pd
import numpy as np
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from .config import config
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from app.services.dataset_generator.dataset_validator import DatasetValidator

class Trainer:
    def __init__(self, artifacts_dir: str = config.ARTIFACTS_DIR):
        self.artifacts_dir = artifacts_dir
        
    def _objective(self, trial, X_train, y_train, X_val, y_val):
        params = {
            "objective": "reg:squarederror",
            "eval_metric": "rmse",
            "max_depth": trial.suggest_int("max_depth", 3, 9),
            "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0)
        }
        
        if XGB_AVAILABLE:
            model = xgb.XGBRegressor(**params, random_state=42)
        else:
            model = RandomForestRegressor(max_depth=params["max_depth"], n_estimators=params["n_estimators"], random_state=42)
            
        model.fit(X_train, y_train)
        
        preds = model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        return rmse

    def train(self, dataset_path: str, version: str = None):
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset {dataset_path} not found.")
            
        print(f"Validating dataset from {dataset_path}...")
        validator = DatasetValidator(dataset_path)
        if not validator.validate():
            report = validator.get_report()
            raise ValueError(f"Dataset Validation Failed! Report: {json.dumps(report, indent=2)}")
            
        print(f"Dataset is valid. Loading...")
        df = pd.read_csv(dataset_path)
        
        # Ensure target RRT exists
        if "rrt" not in df.columns:
            raise ValueError("Target column 'rrt' not found in dataset.")
            
        # Parse JSON features
        import json
        df['parsed_features'] = df['rrfe_features'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        features = [
            "temporal_freshness",
            "temporal_availability",
            "source_credibility",
            "evidence_consistency",
            "evidence_sufficiency",
        ]
        
        for feat in features:
            df[feat] = df['parsed_features'].apply(lambda x: x.get(feat, 0.5) if isinstance(x, dict) else 0.5)
            
        X = df[features].fillna(0.5).values
        y = df["rrt"].values
        
        # Remove NaNs
        valid_indices = ~np.isnan(y)
        X = X[valid_indices]
        y = y[valid_indices]
        
        if len(y) < 10:
            raise ValueError(f"Not enough valid samples to train. Found {len(y)}")
        
        # 1. Train / Validation / Test split (70 / 15 / 15)
        print("Splitting dataset (70/15/15)...")
        X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.1765, random_state=42) # 0.15 / 0.85
        
        # 2. Optuna HPO
        print("Running Optuna hyperparameter optimization...")
        study = optuna.create_study(direction="minimize")
        study.optimize(lambda trial: self._objective(trial, X_train, y_train, X_val, y_val), n_trials=20)
        
        best_params = study.best_params
        best_params["objective"] = "reg:squarederror"
        best_params["eval_metric"] = "rmse"
        print(f"Best params: {best_params}")
        
        # 3. Train final model on Train + Val
        print("Training final model on Train+Val...")
        X_train_full = np.vstack((X_train, X_val))
        y_train_full = np.concatenate((y_train, y_val))
        
        if XGB_AVAILABLE:
            final_model = xgb.XGBRegressor(**best_params, random_state=42)
        else:
            final_model = RandomForestRegressor(max_depth=best_params["max_depth"], n_estimators=best_params["n_estimators"], random_state=42)
            
        final_model.fit(X_train_full, y_train_full)
        
        # 4. Evaluation on held-out Test set
        print("Evaluating on Test set...")
        preds = final_model.predict(X_test)
        
        metrics = {
            "mae": float(mean_absolute_error(y_test, preds)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
            "r2_score": float(r2_score(y_test, preds)),
            "mean_predicted": float(np.mean(preds)),
            "test_samples": len(y_test)
        }
        print(f"Metrics: {metrics}")
        
        # 5. Serialization
        if not version:
            # Generate a date-based semantic version if not provided
            now = datetime.datetime.utcnow()
            version = f"v{now.strftime('%Y.%m.%d')}.{uuid.uuid4().hex[:4]}"
            
        version_dir = os.path.join(self.artifacts_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        
        # Save XGBoost Native JSON
        model_path = os.path.join(version_dir, "model.json")
        if XGB_AVAILABLE:
            final_model.get_booster().save_model(model_path)
        else:
            # Drop mock JSON for end-to-end testing
            with open(model_path, "w") as f:
                json.dump({"mock": True, "model": "RandomForestRegressor"}, f)
        print(f"Model saved to {model_path}")
        
        # Save metrics
        with open(os.path.join(version_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=4)
            
        # Save metadata
        metadata = {
            "model_version": version,
            "training_date": datetime.datetime.utcnow().isoformat(),
            "optuna_params": best_params,
            "features": features,
            "feature_count": len(features),
        }
        with open(os.path.join(version_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
            
        print("Training complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="dataset_ragguard_tr.csv")
    parser.add_argument("--version", type=str, default=None)
    args = parser.parse_args()
    
    trainer = Trainer()
    trainer.train(args.dataset, args.version)
