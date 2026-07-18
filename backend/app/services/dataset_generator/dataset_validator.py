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
        
        # 1. Check for NaNs
        nan_counts = self.df.isna().sum().to_dict()
        self.report["nan_counts"] = nan_counts
        if any(v > (len(self.df) * 0.1) for v in nan_counts.values()):
            # If more than 10% NaNs in any column
            self.report["error_nan"] = "Too many NaN values in dataset"
            is_valid = False
            
        # 2. Check for constant features (zero variance)
        features_to_check = ['tff', 'scf', 'ecf', 'esf', 'rrt']
        zero_variance_cols = []
        for col in features_to_check:
            if col in self.df.columns:
                std_dev = self.df[col].std()
                if pd.isna(std_dev) or std_dev == 0.0:
                    zero_variance_cols.append(col)
                    
        self.report["zero_variance_cols"] = zero_variance_cols
        if zero_variance_cols:
            self.report["error_variance"] = f"Constant features detected (variance=0): {zero_variance_cols}"
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
