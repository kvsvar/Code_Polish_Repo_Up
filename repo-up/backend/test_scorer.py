"""
test_scorer.py — unit tests for thresholds and scorer (no test framework needed).
Run from backend/: python test_scorer.py
"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.metrics.thresholds import rate_metric
from analysis.scorer import compute_repo_score


def main() -> None:  # noqa: C901
    print("=== test_scorer.py ===\n")

    # ------------------------------------------------------------------
    # rate_metric boundary tests
    # ------------------------------------------------------------------
    print("--- rate_metric boundaries ---")

    # LCOM proxy: good <= 0, regular <= 20
    assert rate_metric("lcom", 0)  == "good",    "lcom=0 should be good"
    assert rate_metric("lcom", 5)  == "regular", "lcom=5 should be regular"
    assert rate_metric("lcom", 20) == "regular", "lcom=20 should be regular"
    assert rate_metric("lcom", 21) == "bad",     "lcom=21 should be bad"
    print("LCOM proxy thresholds OK.")

    # DIT: typical=2 → good; 3 → regular; 4 → bad
    assert rate_metric("dit", 1) == "good",    "dit=1 should be good"
    assert rate_metric("dit", 2) == "good",    "dit=2 should be good"
    assert rate_metric("dit", 3) == "regular", "dit=3 should be regular"
    assert rate_metric("dit", 4) == "bad",     "dit=4 should be bad"
    print("DIT thresholds OK.")

    # WMC proxy: good <= 10, regular <= 40
    assert rate_metric("public_methods", 10) == "good",    "wmc=10 should be good"
    assert rate_metric("public_methods", 40) == "regular", "wmc=40 should be regular"
    assert rate_metric("public_methods", 41) == "bad",     "wmc=41 should be bad"
    print("WMC proxy thresholds OK.")

    # COF
    assert rate_metric("cof", 0.01) == "good",    "cof=0.01 should be good"
    assert rate_metric("cof", 0.10) == "regular", "cof=0.10 should be regular"
    assert rate_metric("cof", 0.20) == "bad",     "cof=0.20 should be bad"
    print("COF thresholds OK.")

    # Unknown metric should not crash
    result = rate_metric("nonexistent_metric", 99.9)
    assert result == "good", "Unknown metric should default to 'good'"
    print("Unknown metric fallback OK.")

    # ------------------------------------------------------------------
    # compute_repo_score
    # ------------------------------------------------------------------
    print("\n--- compute_repo_score ---")

    good_metrics = {
        "cof": 0.01,
        "avg_afferent": 1.0,
        "avg_public_fields": 0.0,
        "avg_public_methods": 5.0,
        "avg_dit": 1.0,
        "avg_lcom": 0.0,
    }
    bad_metrics = {
        "cof": 0.50,
        "avg_afferent": 30.0,
        "avg_public_fields": 15.0,
        "avg_public_methods": 50.0,
        "avg_dit": 5.0,
        "avg_lcom": 25.0,
    }

    good_result = compute_repo_score(good_metrics, structural_score=95, security_score=100)
    bad_result  = compute_repo_score(bad_metrics,  structural_score=30, security_score=20)

    print(f"Good repo score: {good_result['final_score']}")
    print(f"Bad  repo score: {bad_result['final_score']}")

    assert good_result["final_score"] > bad_result["final_score"], \
        "Good metrics should outscore bad metrics"

    diff = good_result["final_score"] - bad_result["final_score"]
    assert diff >= 20, f"Score gap should be >= 20 points, got {diff}"
    print(f"Score gap: {diff:.1f} -- OK (>= 20 required).")

    # All scores clamped
    assert 0 <= good_result["final_score"] <= 100
    assert 0 <= bad_result["final_score"]  <= 100
    print("Score clamping OK.")

    # Empty repo (no classes) should not crash
    empty_result = compute_repo_score({}, structural_score=100, security_score=100)
    assert 0 <= empty_result["final_score"] <= 100
    print("Empty-repo (no keys) does not crash — OK.")

    print(f"\nFull good result:\n{json.dumps(good_result, indent=2)}")
    print("\n=== All scorer tests passed ===")


if __name__ == "__main__":
    main()
