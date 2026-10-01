import os
import re
from typing import Dict, Any

SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|token|password|secret)["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-\.]{10,})["\']'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'-----BEGIN PRIVATE KEY-----[\s\S]*?-----END PRIVATE KEY-----')
]

def redact_secrets(text: str) -> str:
    """Redacts common secret patterns from context before sending to LLM."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(r'[REDACTED_SECRET]', text)
    return text

def build_context(finding: dict, project_root: str) -> dict:
    """
    Builds context for LLM prompt.
    Includes rule, CWE, message, and redacted source snippet.
    Never sends full repository or .env files.
    """
    context = {
        "rule": finding.get("rule_id", "UNKNOWN"),
        "cwe": finding.get("cwe", "None"),
        "message": finding.get("description", ""),
        "file": finding.get("file", ""),
        "line": finding.get("line", 1),
        "source_snippet": ""
    }
    
    file_path = finding.get("file")
    line_num = finding.get("line")
    
    if file_path and line_num:
        # Strict exclusion of .env or private files
        if file_path.endswith('.env') or 'secret' in file_path.lower():
            context["source_snippet"] = "[File excluded for privacy]"
            return context
            
        full_path = os.path.join(project_root, file_path)
        # Prevent traversal
        if os.path.abspath(full_path).startswith(os.path.abspath(project_root)):
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    # Provide targeted region context (+/- 15 lines)
                    start = max(0, line_num - 1 - 15)
                    end = min(len(lines), line_num - 1 + 15)
                    
                    snippet = "".join(lines[start:end])
                    context["source_snippet"] = redact_secrets(snippet)
                except Exception:
                    pass
                    
    return context
