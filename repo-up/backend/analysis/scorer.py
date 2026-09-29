"""
scorer.py — maps CK-style metric averages to an ISO/IEC 25010-aligned score.

Scoring formula (documented here so it can be defended)
--------------------------------------------------------
final_score = 0.50 × metrics_score
            + 0.30 × structural_score
            + 0.20 × security_score

All component scores are 0-100.  The final score is clamped to [0, 100].

Metrics used (proxies — see thresholds.py for sources)
-------------------------------------------------------
- COF  (Coupling Factor)          — file-graph connectivity ratio
- Afferent couplings (avg)        — average in-degree per file (Ca proxy)
- Public fields (avg)             — average public attribute count per class
- Public methods (avg)            — WMC proxy (weighted method count)
- DIT (avg)                       — average depth of inheritance tree
- LCOM (avg)                      — cohesion proxy (methods − 1 per class)

ISO 25010 sub-characteristic mapping
--------------------------------------
Modularity   ← COF, afferent couplings
Analysability ← public methods (WMC proxy), public fields
Modifiability ← LCOM proxy
Testability   ← DIT, LCOM proxy
"""

from analysis.metrics.thresholds import rate_metric

ISO_25010_WEIGHTS: dict[str, float] = {
    "modularity":     0.30,  # COF + afferent couplings
    "analysability":  0.25,  # WMC proxy + public fields
    "modifiability":  0.25,  # LCOM proxy
    "testability":    0.20,  # DIT + LCOM proxy
}

BAND_SCORE: dict[str, float] = {"good": 100.0, "regular": 60.0, "bad": 20.0}


def compute_repo_score(
    repo_metrics: dict,
    structural_score: int | float,
    security_score: int | float = 100,
) -> dict:
    """Compute the composite readiness score and ISO 25010 category breakdown.

    Parameters
    ----------
    repo_metrics:
        Averaged metric values across the repo.
        Expected keys:
            cof, avg_afferent, avg_public_fields, avg_public_methods,
            avg_dit, avg_lcom
        Missing or zero values degrade gracefully (default to "good").
    structural_score:
        0-100 score from structural rules (penalty-based, already clamped).
    security_score:
        0-100 score from security checks (penalty-based, already clamped).
    """
    # Clamp inputs
    structural_score = max(0.0, min(100.0, float(structural_score)))
    security_score = max(0.0, min(100.0, float(security_score)))

    # Rate each metric (default "good" if key missing to avoid crash on empty repo)
    ratings: dict[str, str] = {
        "cof":               rate_metric("cof",              repo_metrics.get("cof", 0.0)),
        "afferent_couplings": rate_metric("afferent_couplings", repo_metrics.get("avg_afferent", 0.0)),
        "public_fields":     rate_metric("public_fields",    repo_metrics.get("avg_public_fields", 0.0)),
        "public_methods":    rate_metric("public_methods",   repo_metrics.get("avg_public_methods", 0.0)),
        "dit":               rate_metric("dit",              repo_metrics.get("avg_dit", 1.0)),
        "lcom":              rate_metric("lcom",             repo_metrics.get("avg_lcom", 0.0)),
    }

    band: dict[str, float] = {k: BAND_SCORE[v] for k, v in ratings.items()}

    category_scores: dict[str, float] = {
        "modularity":     (band["afferent_couplings"] + band["cof"]) / 2,
        "analysability":  (band["public_methods"] + band["public_fields"]) / 2,
        "modifiability":  band["lcom"],
        "testability":    (band["dit"] + band["lcom"]) / 2,
    }

    metrics_score: float = sum(
        category_scores[cat] * weight
        for cat, weight in ISO_25010_WEIGHTS.items()
    )

    final_score = (
        metrics_score * 0.5
        + structural_score * 0.3
        + security_score * 0.2
    )

    # Clamp output
    final_score = max(0.0, min(100.0, final_score))

    return {
        "final_score":        round(final_score, 1),
        "structural_score":   round(structural_score, 1),
        "security_score":     round(security_score, 1),
        "metrics_score":      round(metrics_score, 1),
        "category_breakdown": {k: round(v, 1) for k, v in category_scores.items()},
        "metric_ratings":     ratings,
    }
