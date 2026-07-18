import os
import json
from .config import config

class ModelRegistry:
    def __init__(self, artifacts_dir: str = config.ARTIFACTS_DIR):
        self.artifacts_dir = artifacts_dir
        # Ensure dir exists
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
    def list_versions(self) -> list[str]:
        if not os.path.exists(self.artifacts_dir):
            return []
        versions = [d for d in os.listdir(self.artifacts_dir) if os.path.isdir(os.path.join(self.artifacts_dir, d))]
        # Basic semver sort
        versions.sort(key=lambda s: [str(u).zfill(10) for u in s.replace('v', '').split('.')] if s.startswith('v') else [s])
        return versions
        
    def get_latest_version(self) -> str:
        versions = self.list_versions()
        if not versions:
            raise FileNotFoundError("No models found in registry.")
        return versions[-1]

    def get_model_path(self, version: str) -> str:
        if version == "latest":
            version = self.get_latest_version()
        return os.path.join(self.artifacts_dir, version, "model.json")
