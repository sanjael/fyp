try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import xgboost as xgb
except ImportError:
    xgb = None
import numpy as np
from typing import Dict, Any

class Explainer:
    def get_local_importance(self, model: Any, features_array: np.ndarray) -> Dict[str, float]:
        """
        Calculates local SHAP values for a single prediction.
        """
        try:
            if not SHAP_AVAILABLE:
                return {}
            # Initialize TreeExplainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(features_array)
            
            # Map SHAP values to feature names
            feature_names = ["tff", "scf", "ecf", "esf"]
            
            # For a single prediction, shap_values is an array of shape (1, num_features)
            if len(shap_values.shape) == 2:
                vals = shap_values[0]
            else:
                vals = shap_values
                
            return {name: float(val) for name, val in zip(feature_names, vals)}
            
        except Exception as e:
            print(f"SHAP local explanation failed: {e}")
            return {}
