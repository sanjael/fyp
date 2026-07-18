import os
import json
import csv
from typing import List
from ..models import FinalDatasetRow

class MultiExporter:
    def __init__(self, export_dir: str):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        
    def export(self, row: FinalDatasetRow, dataset_name: str):
        """
        Exports a single row to CSV and JSONL simultaneously.
        In a real massive batch pipeline, this would batch rows before flushing.
        """
        csv_path = os.path.join(self.export_dir, f"{dataset_name}_training.csv")
        jsonl_path = os.path.join(self.export_dir, f"{dataset_name}_training.jsonl")
        
        row_dict = row.model_dump()
        
        # Flatten for CSV
        csv_row = row_dict.copy()
        for k, v in csv_row.items():
            if isinstance(v, (list, dict)):
                csv_row[k] = json.dumps(v)
            elif hasattr(v, "isoformat"):
                csv_row[k] = v.isoformat()
                
        # 1. Append CSV
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(csv_row)
            
        # 2. Append JSONL
        with open(jsonl_path, mode='a', encoding='utf-8') as f:
            # Need to convert datetime for JSON
            json_row = row.model_dump(mode='json')
            f.write(json.dumps(json_row) + "\n")
