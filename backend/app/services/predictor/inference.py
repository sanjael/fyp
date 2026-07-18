import time
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
from typing import Dict, Optional

from .config import config
from .model_loader import ModelLoader
from .feature_preprocessor import FeaturePreprocessor
from .validation import PredictionValidator
from .models import InferenceResponse
from .explainability import Explainer

class PredictorEngine:
    def __init__(self):
        self.loader = ModelLoader()
        self.preprocessor = FeaturePreprocessor()
        self.validator = PredictionValidator()
        self.explainer = Explainer() if config.ENABLE_SHAP else None

    def predict(self, rrfe_features: dict, version: str = "latest") -> InferenceResponse:
        start_time = time.time()
        
        try:
            # 1. Load cached model
            model, actual_version = self.loader.load_model(version)
            
            # 2. Preprocess features
            features_array = self.preprocessor.transform(rrfe_features)
            
            # 3. Predict
            if XGB_AVAILABLE:
                # Convert to DMatrix for prediction
                dmatrix = xgb.DMatrix(features_array)
                preds = model.predict(dmatrix)
                raw_trri = float(preds[0])
            else:
                # Mock prediction for fallback model
                import numpy as np
                raw_trri = float(np.mean(features_array))
            
            # 4. Validate & Monitor
            safe_trri, drift_flags = self.validator.validate_prediction(raw_trri)
            
            # 5. Explainability (Optional)
            shap_values = None
            if self.explainer:
                shap_values = self.explainer.get_local_importance(model, features_array)
                
        except Exception as e:
            print(f"Prediction failed: {e}")
            # Safe fallback on catastrophic failure
            safe_trri = 0.5
            actual_version = "fallback"
            drift_flags = ["prediction_failure"]
            shap_values = None

        latency_ms = (time.time() - start_time) * 1000
        
        # 6. Build Metadata and Return
        metadata = self.validator.build_metadata(latency_ms, actual_version, drift_flags)
        
        return InferenceResponse(
            trri=safe_trri,
            metadata=metadata,
            shap_values=shap_values
        )

# Singleton instance
predictor_engine = PredictorEngine()
