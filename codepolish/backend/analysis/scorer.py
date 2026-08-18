"""
Category mapping per ISO/IEC 25010 maintainability sub-characteristics.
"""

from analysis.metrics.thresholds import rate_metric

ISO_25010_WEIGHTS = {
    "modularity":     0.30,  # driven by afferent_couplings, cof
    "analysability":  0.25,  # driven by public_methods, public_fields
    "modifiability":  0.25,  # driven by lcom, wmc
    "testability":    0.20,  # driven by dit, wmc
}

BAND_SCORE = {"good": 100, "regular": 60, "bad": 20}

def compute_repo_score(repo_metrics: dict, structural_score: int) -> dict:
    """
    repo_metrics: dict of averaged metric values across the repo, e.g.
        {"cof": 0.01, "avg_afferent": 3.2, "avg_public_fields": 1.1,
         "avg_public_methods": 8.4, "avg_dit": 1.0, "avg_lcom": 4.5}
    structural_score: existing 0-100 score from structural.py
    """
    ratings = {
        "cof": rate_metric("cof", repo_metrics["cof"]),
        "afferent_couplings": rate_metric("afferent_couplings", repo_metrics["avg_afferent"]),
        "public_fields": rate_metric("public_fields", repo_metrics["avg_public_fields"]),
        "public_methods": rate_metric("public_methods", repo_metrics["avg_public_methods"]),
        "dit": rate_metric("dit", repo_metrics["avg_dit"]),
        "lcom": rate_metric("lcom", repo_metrics["avg_lcom"]),
    }
    band = {k: BAND_SCORE[v] for k, v in ratings.items()}

    category_scores = {
        "modularity":    (band["afferent_couplings"] + band["cof"]) / 2,
        "analysability": (band["public_methods"] + band["public_fields"]) / 2,
        "modifiability": band["lcom"],
        "testability":   (band["dit"] + band["lcom"]) / 2,
    }

    metrics_score = sum(
        category_scores[cat] * weight
        for cat, weight in ISO_25010_WEIGHTS.items()
    )

    # Final: 60% CK-metric/ISO score, 40% existing structural checklist score.
    # This weighting is a project decision — document it in the report.
    final_score = round(metrics_score * 0.6 + structural_score * 0.4, 1)

    return {
        "final_score": final_score,
        "structural_score": structural_score,
        "metrics_score": round(metrics_score, 1),
        "category_breakdown": {k: round(v, 1) for k, v in category_scores.items()},
        "metric_ratings": ratings,
    }
