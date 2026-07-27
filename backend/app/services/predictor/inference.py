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


class ModelNotTrainedError(RuntimeError):
    """
    Raised when no trained TRRI model exists in the artifact registry.
    Evaluation must not proceed without a valid trained model.
    """
    pass


class PredictorEngine:
    def __init__(self):
        self.loader = ModelLoader()
        self.preprocessor = FeaturePreprocessor()
        self.validator = PredictionValidator()
        self.explainer = Explainer() if config.ENABLE_SHAP else None

    def predict(self, rrfe_features: dict, version: str = "latest") -> InferenceResponse:
        start_time = time.time()

        # 1. Check for missing scientific features (Scientific Integrity Rule)
        missing = self.preprocessor.get_missing_features(rrfe_features)
        if missing:
            latency_ms = (time.time() - start_time) * 1000
            metadata = self.validator.build_metadata(latency_ms, version, [f"missing_features: {missing}"])
            return InferenceResponse(
                trri=None,
                is_available=False,
                missing_features=missing,
                reason=f"Prediction unavailable: the following RRFE features have no valid score: {missing}. Substituting 0.5 is forbidden to maintain scientific validity.",
                metadata=metadata,
                shap_values=None,
            )

        # 2. Load model — raises ModelNotTrainedError if no trained model exists.
        model, actual_version = self._load_or_raise(version)

        # 3. Preprocess features
        features_array = self.preprocessor.transform(rrfe_features)

        # 3. Predict
        if XGB_AVAILABLE:
            import xgboost as xgb
            dmatrix = xgb.DMatrix(features_array)
            preds = model.predict(dmatrix)
            raw_trri = float(preds[0])
        else:
            # XGBoost is not installed — cannot produce a valid prediction.
            raise ModelNotTrainedError(
                "XGBoost is not installed. "
                "Install xgboost and train the TRRI model before running evaluation."
            )

        # 4. Validate & monitor
        safe_trri, drift_flags = self.validator.validate_prediction(raw_trri)

        # 5. Explainability (optional)
        shap_values = None
        if self.explainer:
            try:
                shap_values = self.explainer.get_local_importance(model, features_array)
            except Exception as shap_exc:
                # SHAP failure must not silently corrupt the prediction
                drift_flags.append(f"shap_failed: {shap_exc}")

        latency_ms = (time.time() - start_time) * 1000
        metadata = self.validator.build_metadata(latency_ms, actual_version, drift_flags)

        return InferenceResponse(
            trri=safe_trri,
            metadata=metadata,
            shap_values=shap_values,
        )

    def _load_or_raise(self, version: str):
        """
        Load the trained model from the artifact registry.
        Raises ModelNotTrainedError with a clear message if no model is found.
        Never falls back to a heuristic or averaging.
        """
        try:
            return self.loader.load_model(version)
        except FileNotFoundError as exc:
            raise ModelNotTrainedError(
                "Trained TRRI model not found. "
                "Please train the model before running evaluation.\n"
                f"  Train command: python -m app.services.predictor.train --dataset <path>\n"
                f"  Artifact directory: {config.ARTIFACTS_DIR}\n"
                f"  Original error: {exc}"
            ) from exc


# Singleton instance
predictor_engine = PredictorEngine()
