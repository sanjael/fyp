from pydantic_settings import BaseSettings

class PredictorConfig(BaseSettings):
    ARTIFACTS_DIR: str = "app/services/predictor/artifacts"
    DEFAULT_MODEL_VERSION: str = "latest"
    TRRI_MIN: float = 0.0
    TRRI_MAX: float = 1.0
    
    # SHAP Config
    ENABLE_SHAP: bool = False

config = PredictorConfig()
