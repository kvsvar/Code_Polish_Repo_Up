import os
import json
import csv
from typing import List
from .schema import DatasetRecord

def export_jsonl(records: List[DatasetRecord], filepath: str):
    """Exports records to a JSONL file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r.to_dict()) + "\n")

def export_csv_summary(records: List[DatasetRecord], filepath: str):
    """Exports a non-sensitive summary to CSV."""
    if not records:
        return
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["repository_id", "language", "file", "rule", "cwe", "final_status", "original_code_hash", "patched_code_hash"])
        for r in records:
            writer.writerow([
                r.repository_id,
                r.language,
                r.file,
                r.rule,
                r.cwe or "",
                r.final_status,
                r.original_code_hash,
                r.patched_code_hash or ""
            ])

def export_markdown_stats(records: List[DatasetRecord], filepath: str):
    """Exports dataset statistics to Markdown."""
    lang_counts = {}
    rule_counts = {}
    cwe_counts = {}
    status_counts = {}
    
    for r in records:
        lang_counts[r.language] = lang_counts.get(r.language, 0) + 1
        rule_counts[r.rule] = rule_counts.get(r.rule, 0) + 1
        if r.cwe:
            cwe_counts[r.cwe] = cwe_counts.get(r.cwe, 0) + 1
        status_counts[r.final_status] = status_counts.get(r.final_status, 0) + 1
        
    md = ["# Repo-Up Dataset Statistics\n"]
    
    md.append("## By Final Status")
    for k, v in sorted(status_counts.items(), key=lambda x: -x[1]):
        md.append(f"- {k}: {v}")
        
    md.append("\n## By Language")
    for k, v in sorted(lang_counts.items(), key=lambda x: -x[1]):
        md.append(f"- {k}: {v}")
        
    md.append("\n## By Rule")
    for k, v in sorted(rule_counts.items(), key=lambda x: -x[1]):
        md.append(f"- {k}: {v}")
        
    md.append("\n## By CWE")
    for k, v in sorted(cwe_counts.items(), key=lambda x: -x[1]):
        md.append(f"- {k}: {v}")
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))
