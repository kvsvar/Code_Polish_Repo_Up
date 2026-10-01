from typing import List, Tuple
from analysis.finding import Finding
from .ground_truth import ExpectedFinding

def match_finding(expected: ExpectedFinding, actual: Finding, line_tolerance: int = 3) -> bool:
    """
    Determines if an actual finding matches the expected finding.
    Rules:
    - Rule ID or CWE must match or be equivalent.
    - File path must match (ignoring leading relative paths / slashes).
    - Line must be within line_tolerance (e.g. +/- 3 lines), unless line is not specified.
    """
    if expected.rule != actual.rule_id and expected.rule != actual.cwe and expected.rule != actual.rule:
        return False
        
    # File match
    expected_file = expected.file.replace("\\", "/").strip("/")
    actual_file = (actual.file or "").replace("\\", "/").strip("/")
    if not actual_file.endswith(expected_file):
        return False
        
    # Line match
    if expected.line is not None and actual.line is not None:
        if abs(expected.line - actual.line) > line_tolerance:
            return False
            
    return True

def compute_matches(expected_list: List[ExpectedFinding], actual_list: List[Finding], line_tolerance: int = 3) -> Tuple[List[ExpectedFinding], List[Finding], List[ExpectedFinding]]:
    """
    Computes matches between expected and actual findings.
    Returns: (matched_expected, unmatched_actual (FP), unmatched_expected (FN))
    """
    unmatched_actual = list(actual_list)
    unmatched_expected = list(expected_list)
    matched_expected = []
    
    # Simple greedy match
    for exp in expected_list:
        best_match = None
        for act in unmatched_actual:
            if match_finding(exp, act, line_tolerance):
                best_match = act
                break
        
        if best_match:
            matched_expected.append(exp)
            unmatched_actual.remove(best_match)
            unmatched_expected.remove(exp)
            
    return matched_expected, unmatched_actual, unmatched_expected
