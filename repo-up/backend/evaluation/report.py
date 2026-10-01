import json
import csv
from datetime import datetime
from typing import List, Dict, Any
from analysis.finding import Finding
from .ground_truth import BenchmarkManifest, ExpectedFinding
from .metrics import calculate_metrics

def generate_evaluation_report(
    manifest: BenchmarkManifest,
    matched: List[ExpectedFinding],
    unmatched_actual: List[Finding], # FP
    unmatched_expected: List[ExpectedFinding], # FN
    repo_up_version: str = "1.0",
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    
    config = config or {}
    
    # 1. Total Metrics
    tp = len(matched)
    fp = len(unmatched_actual)
    fn = len(unmatched_expected)
    overall_metrics = calculate_metrics(tp, fp, fn)
    
    # 2. Category Metrics
    def get_category(rule_id: str) -> str:
        if rule_id.startswith("SEC-") or rule_id.startswith("CODEQL-"):
            return "Security"
        elif rule_id.startswith("STRUCT-"):
            return "Structural"
        elif rule_id.startswith("SMELL-") or rule_id.startswith("CODE-"):
            return "Code Smell"
        return "Unknown"

    categories = {
        "Security": {"tp":0, "fp":0, "fn":0}, 
        "Structural": {"tp":0, "fp":0, "fn":0}, 
        "Code Smell": {"tp":0, "fp":0, "fn":0}
    }
    
    for m in matched:
        cat = get_category(m.rule)
        if cat in categories: categories[cat]["tp"] += 1
    for fp_act in unmatched_actual:
        cat = get_category(fp_act.rule_id)
        if cat in categories: categories[cat]["fp"] += 1
    for fn_exp in unmatched_expected:
        cat = get_category(fn_exp.rule)
        if cat in categories: categories[cat]["fn"] += 1
        
    for cat, counts in categories.items():
        counts.update(calculate_metrics(counts["tp"], counts["fp"], counts["fn"]))

    # 3. Rule Metrics
    rule_stats = {}
    
    def add_rule_stat(rule: str, tp_inc=0, fp_inc=0, fn_inc=0):
        if rule not in rule_stats:
            rule_stats[rule] = {"tp": 0, "fp": 0, "fn": 0}
        rule_stats[rule]["tp"] += tp_inc
        rule_stats[rule]["fp"] += fp_inc
        rule_stats[rule]["fn"] += fn_inc
        
    for m in matched: add_rule_stat(m.rule, tp_inc=1)
    for fp_act in unmatched_actual: add_rule_stat(fp_act.rule_id, fp_inc=1)
    for fn_exp in unmatched_expected: add_rule_stat(fn_exp.rule, fn_inc=1)
    
    for rule, counts in rule_stats.items():
        counts.update(calculate_metrics(counts["tp"], counts["fp"], counts["fn"]))

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo_up_version": repo_up_version,
        "language": manifest.language,
        "dataset_version": manifest.dataset_version,
        "configuration": config,
        "overall_metrics": {
            "expected_findings": len(manifest.expected_findings),
            "detected_findings": tp + fp,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": overall_metrics["precision"],
            "recall": overall_metrics["recall"],
            "f1": overall_metrics["f1"]
        },
        "category_metrics": categories,
        "rule_metrics": rule_stats
    }
    
    return report

def export_manual_validation_csv(actual_findings: List[Finding], out_path: str):
    """
    Exports findings to CSV for manual validation.
    """
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["finding_id", "rule", "language", "file", "line", "message", "review_status"])
        for i, finding in enumerate(actual_findings):
            writer.writerow([
                f"FINDING-{i+1}",
                finding.rule_id,
                finding.language or "Unknown",
                finding.file,
                finding.line,
                finding.description,
                ""
            ])
