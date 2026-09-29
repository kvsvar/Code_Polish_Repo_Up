import json
import os

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}
