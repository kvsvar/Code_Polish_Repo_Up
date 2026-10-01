from typing import Dict

def calculate_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """
    Calculates precision, recall, and F1 score without internal rounding.
    Returns unrounded floats.
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def calculate_pass_at_k(k: int, c: int, n: int) -> float:
    """
    Paper-inspired metric: pass@k.
    Probability that at least one of the top k generated candidates passes the tests.
    n: total candidates generated
    c: number of correct candidates
    """
    if n == 0 or k > n:
        return 0.0
    if n - c < k:
        return 1.0
    # pass@k = 1 - [ (n-c) choose k ] / [ n choose k ]
    prob = 1.0
    for i in range(k):
        prob *= (n - c - i) / (n - i)
    return 1.0 - prob

def calculate_secure_at_k(k: int, s: int, n: int) -> float:
    """
    Paper-inspired metric: secure@k.
    Probability that at least one of top k candidates is secure.
    """
    return calculate_pass_at_k(k, s, n)

def calculate_vulnerable_at_k(k: int, v: int, n: int) -> float:
    """
    Paper-inspired metric: vulnerable@k.
    Probability that at least one of top k candidates is vulnerable.
    """
    return calculate_pass_at_k(k, v, n)
