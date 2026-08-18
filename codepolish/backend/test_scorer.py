import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.metrics.thresholds import rate_metric
from analysis.scorer import compute_repo_score

def main():
    print("--- Testing rate_metric boundaries ---")
    
    # LCOM: good <= 0, regular <= 20
    assert rate_metric("lcom", 0) == "good"
    assert rate_metric("lcom", 5) == "regular"
    assert rate_metric("lcom", 20) == "regular"
    assert rate_metric("lcom", 25) == "bad"
    print("LCOM thresholds passed.")
    
    # DIT: typical <= 2
    assert rate_metric("dit", 1) == "good"
    assert rate_metric("dit", 2) == "good"
    assert rate_metric("dit", 3) == "regular"  # typical + 1
    assert rate_metric("dit", 4) == "bad"
    print("DIT thresholds passed.")
    
    # Public Methods: good <= 10, regular <= 40
    assert rate_metric("public_methods", 10) == "good"
    assert rate_metric("public_methods", 40) == "regular"
    assert rate_metric("public_methods", 41) == "bad"
    print("Public Methods thresholds passed.")
    
    print("\n--- Testing compute_repo_score ---")
    
    mock_metrics = {
        "cof": 0.01,                 # good
        "avg_afferent": 3.2,         # regular (<= 20)
        "avg_public_fields": 1.1,    # regular (<= 10)
        "avg_public_methods": 8.4,   # good (<= 10)
        "avg_dit": 1.0,              # good (<= 2)
        "avg_lcom": 4.5              # regular (<= 20)
    }
    
    mock_structural = 85
    
    result = compute_repo_score(mock_metrics, mock_structural)
    
    import json
    print(json.dumps(result, indent=2))
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    main()
