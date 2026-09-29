import os
import re

# Simple pattern matchers for first-pass MVP
SECRET_PATTERNS = {
    "AWS Access Key": r"(?i)AKIA[0-9A-Z]{16}",
    "Generic API Key / Token": r"(?i)(api_key|apikey|token|secret)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
}

def run_security_rules(project_path: str):
    """
    Evaluates the project against defined security and robustness rules.
    Returns: findings (list), penalty (int).
    """
    findings = []
    penalty = 0

    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    
    # 1. Environment validation (Check for committed .env files)
    env_files_found = []
    
    # 2. Hardcoded secret detection
    secrets_found = []

    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        
        for f in filenames:
            # Check for .env files (excluding .env.example)
            if f.startswith('.env') and 'example' not in f and 'sample' not in f and 'template' not in f:
                env_files_found.append(os.path.relpath(os.path.join(dirpath, f), project_path))
                
            # Scan for secrets in source code files
            if f.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.h', '.c', '.json', '.yml', '.yaml')):
                filepath = os.path.join(dirpath, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                        for i, line in enumerate(lines):
                            for secret_type, pattern in SECRET_PATTERNS.items():
                                if re.search(pattern, line):
                                    secrets_found.append({
                                        "file": os.path.relpath(filepath, project_path),
                                        "type": secret_type,
                                        "line": i + 1
                                    })
                except Exception:
                    pass

    if env_files_found:
        findings.append({
            "category": "Security",
            "title": "Committed Environment File",
            "description": f"Found sensitive environment files committed to source control: {', '.join(env_files_found)}",
            "severity": "High"
        })
        penalty += 20

    if secrets_found:
        files_with_secrets = list(set(s["file"] for s in secrets_found))
        
        # Emit individual findings so they can be clicked/jumped to
        for secret in secrets_found:
            findings.append({
                "category": "Security",
                "title": f"Hardcoded Secret: {secret['type']}",
                "description": f"Found potential hardcoded secret in {secret['file']}. Note: This is a rules-based first pass; entropy-based detection is recommended for production.",
                "severity": "High",
                "file": secret["file"],
                "line": secret["line"]
            })
            penalty += 15

    return findings, penalty
