import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.dataset_loader import load_dataset_manifest
from evaluation.matching import compute_matches
from evaluation.report import generate_evaluation_report, export_manual_validation_csv
from analysis.finding import Finding
from analysis.rules.ast_security import run_ast_security_rules
from analysis.rules.structural import run_structural_rules
from analysis.rules.security.security_engine import run_security_engine
from analysis.rules.smells.smell_engine import run_smell_engine

def run_benchmark(manifest_path: str, project_path: str, out_json: str, out_csv: str):
    manifest = load_dataset_manifest(manifest_path)
    
    findings = []
    
    # Run AST security rules
    ast_findings, _ = run_ast_security_rules(project_path)
    findings.extend(ast_findings)
    
    # Run Structural
    struct_findings, _ = run_structural_rules(project_path)
    findings.extend(struct_findings)
    
    # Run Security (Phase 3)
    sec_findings, _ = run_security_engine(project_path)
    findings.extend(sec_findings)
    
    # Run Smells
    smell_findings, _ = run_smell_engine(project_path)
    findings.extend(smell_findings)
    
    actual_findings = []
    for f in findings:
        if isinstance(f, dict):
            actual_findings.append(Finding.from_dict(f))
        elif isinstance(f, Finding):
            actual_findings.append(f)
            
    matched, fp, fn = compute_matches(manifest.expected_findings, actual_findings, line_tolerance=3)
    
    report = generate_evaluation_report(
        manifest=manifest,
        matched=matched,
        unmatched_actual=fp,
        unmatched_expected=fn,
        repo_up_version="Phase 8",
        config={"line_tolerance": 3}
    )
    
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    export_manual_validation_csv(actual_findings, out_csv)
    
    return report
