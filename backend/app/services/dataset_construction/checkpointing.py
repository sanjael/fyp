import os
import json
from typing import Set
from .config import config

class CheckpointManager:
    def __init__(self, filepath: str = config.CHECKPOINT_FILE):
        self.filepath = filepath
        self._processed_ids: Set[str] = set()
        self._load()
        
    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    self._processed_ids = set(data.get("processed_ids", []))
            except Exception:
                pass
                
    def is_processed(self, record_id: str) -> bool:
        return record_id in self._processed_ids
        
    def mark_processed(self, record_id: str):
        self._processed_ids.add(record_id)
        # Flush to disk (can be optimized to batch flushes)
        self.save()
        
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump({"processed_ids": list(self._processed_ids)}, f)
