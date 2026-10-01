import json
import os
from .ground_truth import BenchmarkManifest

def load_dataset_manifest(filepath: str) -> BenchmarkManifest:
    """Loads a benchmark manifest JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Manifest not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return BenchmarkManifest.from_dict(data)
