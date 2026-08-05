import pandas as pd
import numpy as np

class DatasetValidator:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.df = None
        self.report = {}
        
    def validate(self) -> bool:
        try:
            self.df = pd.read_csv(self.dataset_path)
        except Exception as e:
            self.report["error"] = f"Failed to load dataset: {e}"
            return False
            
        is_valid = True
        
        # 1. Target and Feature column verification
        target_col = "trri" if "trri" in self.df.columns else ("rrt" if "rrt" in self.df.columns else None)
        if not target_col:
            self.report["error_target"] = "Neither 'trri' nor 'rrt' target column found in dataset"
            is_valid = False

        features_to_check = [
            'temporal_freshness',
            'temporal_availability',
            'source_credibility',
            'evidence_consistency',
            'evidence_sufficiency',
        ]
        if not any(f in self.df.columns for f in features_to_check):
            features_to_check = ['tff', 'scf', 'ecf', 'esf']

        cols_to_check = features_to_check + ([target_col] if target_col else [])

        # 2. Check for NaNs in feature/target columns
        nan_counts = {c: int(self.df[c].isna().sum()) for c in cols_to_check if c in self.df.columns}
        self.report["nan_counts"] = nan_counts
        if any(v > (len(self.df) * 0.1) for v in nan_counts.values()):
            self.report["error_nan"] = f"Too many NaN values in feature/target columns: {nan_counts}"
            is_valid = False
        zero_variance_cols = []
        for col in cols_to_check:
            if col in self.df.columns:
                std_dev = self.df[col].std()
                if pd.isna(std_dev) or std_dev == 0.0:
                    zero_variance_cols.append(col)
                    
        self.report["zero_variance_cols"] = zero_variance_cols
        if zero_variance_cols:
            self.report["warning_variance"] = f"Constant features detected (variance=0): {zero_variance_cols}"
            # Only fail validation if target column itself is constant or ALL features are constant
            if (target_col and target_col in zero_variance_cols) or len(zero_variance_cols) >= len(features_to_check):
                self.report["error_variance"] = f"Target column or all features have zero variance: {zero_variance_cols}"
                is_valid = False
            
        # 3. Size check (e.g. pilot run should have a reasonable number of samples)
        self.report["total_samples"] = len(self.df)
        if len(self.df) < 10:
            self.report["error_size"] = "Dataset too small for meaningful training"
            is_valid = False
            
        self.report["is_valid"] = is_valid
        return is_valid

    def get_report(self) -> dict:
        return self.report
