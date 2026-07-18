import csv
import json
from typing import List
import os
from .base import BaseExporter
from ..models import DatasetSample

class CSVExporter(BaseExporter):
    def export(self, samples: List[DatasetSample], filepath: str) -> bool:
        if not samples:
            return True
            
        file_exists = os.path.isfile(filepath)
        
        try:
            with open(filepath, mode='a', newline='', encoding='utf-8') as f:
                # We flatten the dictionary for CSV
                fieldnames = list(samples[0].model_dump().keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                    
                for sample in samples:
                    row = sample.model_dump()
                    # Convert dict/lists to json strings for CSV compatibility
                    row['document_ids'] = json.dumps(row['document_ids'])
                    row['retrieved_metadata'] = json.dumps(row['retrieved_metadata'])
                    row['raw_metrics'] = json.dumps(row['raw_metrics'])
                    row['timestamp'] = row['timestamp'].isoformat()
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"CSV Export failed: {e}")
            return False
