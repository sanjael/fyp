try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
import threading
from .model_registry import ModelRegistry

class ModelLoader:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ModelLoader, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.registry = ModelRegistry()
        self.cached_model = None
        self.cached_version = None

    def load_model(self, version: str = "latest"):
        actual_version = self.registry.get_latest_version() if version == "latest" else version
        
        # Return cached model if already loaded
        if self.cached_model is not None and self.cached_version == actual_version:
            return self.cached_model, actual_version
            
        model_path = self.registry.get_model_path(actual_version)
        if XGB_AVAILABLE:
            booster = xgb.Booster()
            booster.load_model(model_path)
            self.cached_model = booster
        else:
            self.cached_model = "mock_model"
            
        self.cached_version = actual_version
        return self.cached_model, actual_version
