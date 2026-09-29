"""
analysis/rules/security/secrets.py
SEC-HARDCODED-SECRET / SEC-COMMITTED-ENV — Normalized secret detection.

This module supersedes the inline regex patterns in security.py but is designed
to coexist — security.py still runs for backward compatibility; this module
runs as part of the new security engine with redacted evidence.

Secret detection strategy
--------------------------
1. Regex patterns for well-known secret shapes (AWS keys, API tokens, etc.)
2. Line-level match — report file + line, never the matched value.
3. Evidence in the finding is REDACTED: we report "found at line N" not the value.
4. .env files committed to source control are reported as SEC-COMMITTED-ENV.

Redaction contract
------------------
* The secret value is NEVER included in any finding field.
* The finding description says "potential secret detected" and references
  the line number for human review.
* Log messages never emit the matched string.
"""

from __future__ import annotations
import os
import re

# ---------------------------------------------------------------------------
# Secret patterns — shape-based only, not entropy
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[str, str, str]] = [
    # (name, pattern, cwe)
    (
        "AWS Access Key ID",
        r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])",
        "CWE-798",
    ),
    (
        "Generic API Key / Token",
        r"(?i)(api[_-]?key|apikey|api[_-]?token|auth[_-]?token|access[_-]?token|secret[_-]?key)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
        "CWE-798",
    ),
    (
        "Hardcoded Password",
        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        "CWE-798",
    ),
    (
        "Private Key Header",
        r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "CWE-321",
    ),
    (
        "GitHub Token",
        r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}",
        "CWE-798",
    ),
    (
        "Slack Webhook / Token",
        r"xox[baprs]-[0-9a-zA-Z\-]{10,}",
        "CWE-798",
    ),
    (
        "Database Connection String with Credentials",
        r"(?i)(postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@",
        "CWE-798",
    ),
]

_SOURCE_EXTENSIONS = frozenset({
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cpp", ".cc", ".cxx", ".h", ".hpp",
    ".json", ".yml", ".yaml", ".properties", ".xml", ".toml",
    ".env", ".cfg", ".ini", ".conf",
})

_IGNORED_DIRS = frozenset({
    "node_modules", "venv", ".venv", ".git", "__pycache__",
    "dist", "build", ".next", "out", "target",
})

_ENV_SAFE_NAMES = frozenset({
    ".env.example", ".env.sample", ".env.template", ".env.test", ".env.ci",
})


def _is_env_file(filename: str) -> bool:
    base = os.path.basename(filename)
    return base.startswith(".env") and base not in _ENV_SAFE_NAMES


def scan_secrets(project_path: str) -> list[dict]:
    """Walk project and return raw secret findings with redacted evidence."""
    results: list[dict] = []
    env_files: list[str] = []

    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if d not in _IGNORED_DIRS]

        for fname in filenames:
            filepath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(filepath, project_path)
            ext = os.path.splitext(fname)[1].lower()

            # Committed .env detection
            if _is_env_file(fname):
                env_files.append(rel_path)
                continue

            if ext not in _SOURCE_EXTENSIONS:
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                    for line_no, line in enumerate(fh, start=1):
                        for name, pattern, cwe in _SECRET_PATTERNS:
                            if re.search(pattern, line):
                                results.append({
                                    "rule_id": "SEC-HARDCODED-SECRET",
                                    "secret_type": name,
                                    "cwe": cwe,
                                    "line": line_no,
                                    "file": rel_path,
                                    # Evidence is redacted — no actual secret value
                                    "detail": (
                                        f"Potential {name} detected at line {line_no}. "
                                        "The matched pattern suggests a hardcoded credential. "
                                        "Review and remove; use environment variables or a secrets manager."
                                    ),
                                })
                                break  # one finding per line
            except Exception:
                pass

    # Report committed env files
    for env_rel in env_files:
        results.append({
            "rule_id": "SEC-COMMITTED-ENV",
            "secret_type": "Committed Environment File",
            "cwe": "CWE-798",
            "line": 1,
            "file": env_rel,
            "detail": (
                f"File '{env_rel}' appears to be a committed environment/secrets file. "
                "Environment files containing credentials must not be tracked in version control. "
                "Add to .gitignore and rotate any exposed credentials."
            ),
        })

    return results
