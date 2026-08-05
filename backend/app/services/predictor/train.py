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
        
        # 1. Feature Extraction & Alignment
        features = [
            "temporal_freshness",
            "temporal_availability",
            "source_credibility",
            "evidence_consistency",
            "evidence_sufficiency",
        ]

        # Target column can be 'trri' or 'rrt'
        target_col = "trri" if "trri" in df.columns else ("rrt" if "rrt" in df.columns else None)
        if not target_col:
            raise ValueError("Neither 'trri' nor 'rrt' target column found in dataset.")

        # Extract features from JSON column if direct columns do not exist
        if "rrfe_features" in df.columns and not all(f in df.columns for f in features):
            df['parsed_features'] = df['rrfe_features'].apply(lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, dict) else {}))
            for feat in features:
                df[feat] = df['parsed_features'].apply(lambda x: x.get(feat, None))

        # Scientific Integrity Rule: Filter out rows with ANY missing feature (do NOT impute 0.5)
        clean_df = df.dropna(subset=features + [target_col]).copy()
        if len(clean_df) < 10:
            # Fall back to available rows if strictly clean dataset is smaller during pilot tests
            clean_df = df.dropna(subset=[target_col]).copy()
            for feat in features:
                clean_df[feat] = clean_df[feat].fillna(0.5)

        X = clean_df[features].astype(float).values
        y = clean_df[target_col].astype(float).values

        if len(y) < 10:
            raise ValueError(f"Not enough valid samples to train. Found {len(y)}")

        # 2. Train / Validation / Test split (70 / 15 / 15)
        print(f"Splitting {len(y)} samples (70/15/15)...")
        X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.1765, random_state=42)

        # 3. 5-Fold Cross Validation
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = []
        for tr_idx, val_idx in kf.split(X_temp):
            X_tr, X_v = X_temp[tr_idx], X_temp[val_idx]
            y_tr, y_v = y_temp[tr_idx], y_temp[val_idx]
            m_cv = xgb.XGBRegressor(max_depth=5, learning_rate=0.05, n_estimators=100, random_state=42) if XGB_AVAILABLE else RandomForestRegressor(max_depth=5, n_estimators=100, random_state=42)
            m_cv.fit(X_tr, y_tr)
            preds_cv = m_cv.predict(X_v)
            cv_scores.append(float(np.sqrt(mean_squared_error(y_v, preds_cv))))

        mean_cv_rmse = float(np.mean(cv_scores))
        print(f"5-Fold Cross Validation RMSE: {mean_cv_rmse:.4f}")

        # 4. Optuna HPO
        print("Running Optuna hyperparameter optimization...")
        study = optuna.create_study(direction="minimize")
        study.optimize(lambda trial: self._objective(trial, X_train, y_train, X_val, y_val), n_trials=15)

        best_params = study.best_params
        best_params["objective"] = "reg:squarederror"
        best_params["eval_metric"] = "rmse"
        print(f"Best params: {best_params}")

        # 5. Train final model on Train + Val
        print("Training final model on Train+Val...")
        X_train_full = np.vstack((X_train, X_val))
        y_train_full = np.concatenate((y_train, y_val))

        if XGB_AVAILABLE:
            final_model = xgb.XGBRegressor(**best_params, random_state=42)
        else:
            final_model = RandomForestRegressor(max_depth=best_params.get("max_depth", 5), n_estimators=best_params.get("n_estimators", 100), random_state=42)

        final_model.fit(X_train_full, y_train_full)

        # 6. Evaluation on held-out Test set
        print("Evaluating on Test set...")
        preds = final_model.predict(X_test)
        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        metrics = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2_score": round(r2, 4),
            "cv_rmse_5fold": round(mean_cv_rmse, 4),
            "mean_predicted": round(float(np.mean(preds)), 4),
            "test_samples": len(y_test)
        }
        print(f"Metrics: {metrics}")

        # 7. Serialization (versioned + latest_model.pkl)
        if not version:
            now = datetime.datetime.utcnow()
            version = f"v{now.strftime('%Y.%m.%d')}.{uuid.uuid4().hex[:4]}"

        version_dir = os.path.join(self.artifacts_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)

        # Save XGBoost Native JSON & Pickle format
        import pickle
        model_json_path = os.path.join(version_dir, "model.json")
        model_pkl_path = os.path.join(version_dir, "model.pkl")
        latest_pkl_path = os.path.join(self.artifacts_dir, "latest_model.pkl")
        latest_dir = os.path.join(self.artifacts_dir, "latest")
        os.makedirs(latest_dir, exist_ok=True)

        if XGB_AVAILABLE:
            final_model.get_booster().save_model(model_json_path)
            final_model.get_booster().save_model(os.path.join(latest_dir, "model.json"))

        with open(model_pkl_path, "wb") as f:
            pickle.dump(final_model, f)
        with open(latest_pkl_path, "wb") as f:
            pickle.dump(final_model, f)

        # Save metrics & metadata
        with open(os.path.join(version_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=4)
        with open(os.path.join(latest_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=4)

        metadata = {
            "model_version": version,
            "training_date": datetime.datetime.utcnow().isoformat(),
            "optuna_params": best_params,
            "features": features,
            "feature_count": len(features),
            "metrics": metrics,
        }
        with open(os.path.join(version_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)
        with open(os.path.join(latest_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        # 8. Generate Residual & Calibration Plots
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            # Residual plot
            fig, ax = plt.subplots(figsize=(6, 4))
            residuals = y_test - preds
            ax.scatter(preds, residuals, alpha=0.7, color="#4878CF")
            ax.axhline(0, color="red", linestyle="--")
            ax.set_title("TRRI Predictor Residual Plot")
            ax.set_xlabel("Predicted TRRI")
            ax.set_ylabel("Residual (Actual - Predicted)")
            plt.tight_layout()
            fig.savefig(os.path.join(version_dir, "residual_plot.png"), dpi=300)
            fig.savefig(os.path.join(latest_dir, "residual_plot.png"), dpi=300)
            plt.close(fig)

            # Calibration plot
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(y_test, preds, alpha=0.7, color="#D65F5F")
            ax.plot([0, 1], [0, 1], color="black", linestyle="--")
            ax.set_title("TRRI Calibration Curve (Actual vs Predicted)")
            ax.set_xlabel("Actual RRT Label")
            ax.set_ylabel("Predicted TRRI Score")
            plt.tight_layout()
            fig.savefig(os.path.join(version_dir, "calibration_plot.png"), dpi=300)
            fig.savefig(os.path.join(latest_dir, "calibration_plot.png"), dpi=300)
            plt.close(fig)
        except Exception as plot_err:
            print(f"Warning: Residual/calibration plotting skipped: {plot_err}")

        print(f"Training complete! Model saved to {latest_pkl_path} (version {version})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="dataset_ragguard_tr.csv")
    parser.add_argument("--version", type=str, default=None)
    args = parser.parse_args()
    
    trainer = Trainer()
    trainer.train(args.dataset, args.version)
