"""
analysis/rules/security/security_engine.py — Phase 3 Security Engine.

Orchestrates all Phase 3 security smell rules against a project directory.
Returns (findings: list[dict], penalty: int) matching the existing contract.

Rules in this engine
--------------------
SEC-CWE-502       Unsafe deserialization (Python/Java/JS)
SEC-WEAK-CRYPTO   Weak hash algorithm usage (all 5 languages)
SEC-UNSAFE-ASSERT Assert as security boundary (Python)
SEC-DANGEROUS-EXEC Dynamic execution / shell injection (all 5 languages)
SEC-CWE-703       Uncovered risky operations / missing exception handling
SEC-HARDCODED-SECRET Hardcoded credentials (all languages, redacted evidence)
SEC-COMMITTED-ENV  .env file committed to source control

Integration with analyze.py
----------------------------
Run as Stage 9 in the event_generator pipeline (after existing security stages).
The existing Stage 3 (regex secrets) and Stage 4 (AST eval/exec) remain but
Phase 3 rules provide richer, CWE-tagged, per-location findings. Duplicates
are possible; the frontend deduplicates visually by file+line.

Penalty weights (added to security_score)
------------------------------------------
SEC-CWE-502        25
SEC-WEAK-CRYPTO    15
SEC-UNSAFE-ASSERT   8
SEC-DANGEROUS-EXEC 20
SEC-CWE-703         5  (per uncovered call, capped)
SEC-HARDCODED-SECRET 15
SEC-COMMITTED-ENV   20

Total security penalty from this engine is soft-capped at 40.
"""

from __future__ import annotations
import logging
import os

from analysis.finding import Finding
from analysis.rule_registry import get as get_rule
from analysis.parsing.ast_parser import parse_file
from analysis.parsing.language_config import LANGUAGE_CONFIG

log = logging.getLogger(__name__)

_IGNORED_DIRS = frozenset({
    "node_modules", "venv", ".venv", ".git", "__pycache__",
    "dist", "build", ".next", "out", "target",
})

_PENALTY = {
    "SEC-CWE-502":            25,
    "SEC-WEAK-CRYPTO":        15,
    "SEC-UNSAFE-ASSERT":       8,
    "SEC-DANGEROUS-EXEC":     20,
    "SEC-CWE-703":             5,
    "SEC-HARDCODED-SECRET":   15,
    "SEC-COMMITTED-ENV":      20,
}
_MAX_PENALTY = 40

# Per-rule caps on findings to prevent explosion
_FINDING_CAPS = {
    "SEC-CWE-703":            8,
    "SEC-DANGEROUS-EXEC":     10,
}


def _get_language(filename: str) -> str:
    for lang, config in LANGUAGE_CONFIG.items():
        if any(filename.endswith(ext) for ext in config["extensions"]):
            return lang
    return ""


def _make_finding(rule_id: str, title: str, description: str, severity: str,
                  file: str = "", line: int = 1, cwe: str | None = None,
                  language: str | None = None) -> dict:
    spec = get_rule(rule_id)
    f = Finding(
        rule_id=rule_id,
        category="Security",
        title=title,
        description=description,
        severity=severity,
        rule=spec.name if spec else rule_id,
        cwe=cwe or (spec.cwe if spec else None),
        resolution=spec.resolution if spec else None,
        language=language,
        file=file or None,
        line=line or None,
        autofix_available=False,
    )
    return f.to_dict()


def run_security_engine(project_path: str) -> tuple[list[dict], int]:
    """Run all Phase 3 security rules on *project_path*.

    Returns (findings: list[dict], penalty: int).
    """
    from .deserialization import (
        analyze_python_deser, analyze_java_deser, analyze_js_deser,
    )
    from .weak_crypto import (
        analyze_python_weak_crypto, analyze_java_weak_crypto,
        analyze_js_weak_crypto, analyze_cpp_weak_crypto,
    )
    from .unsafe_assert import analyze_python_unsafe_assert
    from .dangerous_exec import (
        analyze_python_dangerous_exec, analyze_js_dangerous_exec,
        analyze_java_dangerous_exec, analyze_cpp_dangerous_exec,
    )
    from .exception_handling import (
        analyze_python_exc_handling, analyze_js_exc_handling,
        analyze_java_exc_handling,
    )
    from .secrets import scan_secrets

    findings: list[dict] = []
    penalty = 0
    _rule_counts: dict[str, int] = {}

    def _add(rule_id: str, f: dict) -> None:
        cap = _FINDING_CAPS.get(rule_id, 9999)
        if _rule_counts.get(rule_id, 0) >= cap:
            return
        findings.append(f)
        _rule_counts[rule_id] = _rule_counts.get(rule_id, 0) + 1

    # ----------------------------------------------------------------
    # Secrets scan (text-based, all files)
    # ----------------------------------------------------------------
    try:
        for hit in scan_secrets(project_path):
            rid = hit["rule_id"]
            title = (
                f"Hardcoded Secret: {hit['secret_type']}"
                if rid == "SEC-HARDCODED-SECRET"
                else "Committed Environment File"
            )
            sev = "High" if rid in ("SEC-HARDCODED-SECRET", "SEC-COMMITTED-ENV") else "Medium"
            f = _make_finding(
                rule_id=rid,
                title=title,
                description=hit["detail"],
                severity=sev,
                file=hit.get("file", ""),
                line=hit.get("line", 1),
                cwe=hit.get("cwe"),
            )
            _add(rid, f)
            penalty += _PENALTY.get(rid, 10)
    except Exception:
        log.debug("security_engine: secrets scan failed")

    # ----------------------------------------------------------------
    # Per-file AST-based rules
    # ----------------------------------------------------------------
    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if d not in _IGNORED_DIRS]

        for fname in filenames:
            lang = _get_language(fname)
            if not lang:
                continue

            filepath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(filepath, project_path)

            tree = None
            try:
                tree = parse_file(filepath, lang)
            except Exception:
                log.debug("security_engine: parse failed for %s", filepath)
                continue

            if tree is None:
                continue

            # ---- Dispatch per language ----
            deser_fn = {
                "Python": analyze_python_deser,
                "Java": analyze_java_deser,
                "JavaScript": analyze_js_deser,
                "TypeScript": analyze_js_deser,
            }.get(lang)
            crypto_fn = {
                "Python": analyze_python_weak_crypto,
                "Java": analyze_java_weak_crypto,
                "JavaScript": analyze_js_weak_crypto,
                "TypeScript": analyze_js_weak_crypto,
                "C++": analyze_cpp_weak_crypto,
            }.get(lang)
            exec_fn = {
                "Python": analyze_python_dangerous_exec,
                "JavaScript": analyze_js_dangerous_exec,
                "TypeScript": analyze_js_dangerous_exec,
                "Java": analyze_java_dangerous_exec,
                "C++": analyze_cpp_dangerous_exec,
            }.get(lang)
            assert_fn = {"Python": analyze_python_unsafe_assert}.get(lang)
            exc_fn = {
                "Python": analyze_python_exc_handling,
                "JavaScript": analyze_js_exc_handling,
                "TypeScript": analyze_js_exc_handling,
                "Java": analyze_java_exc_handling,
            }.get(lang)

            # -- CWE-502 Deserialization --
            if deser_fn:
                try:
                    for hit in deser_fn(tree, rel_path):
                        f = _make_finding(
                            rule_id="SEC-CWE-502",
                            title=f"Unsafe Deserialization: {hit['api']}",
                            description=hit["detail"],
                            severity="High",
                            file=rel_path,
                            line=hit["line"],
                            cwe="CWE-502",
                            language=lang,
                        )
                        _add("SEC-CWE-502", f)
                        penalty += _PENALTY["SEC-CWE-502"]
                except Exception:
                    log.debug("security_engine: deserialization failed for %s", rel_path)

            # -- Weak Crypto --
            if crypto_fn:
                try:
                    for hit in crypto_fn(tree, rel_path):
                        f = _make_finding(
                            rule_id="SEC-WEAK-CRYPTO",
                            title=f"Weak Cryptographic Hash: {hit.get('algo', '?')}",
                            description=hit["detail"],
                            severity="Medium",
                            file=rel_path,
                            line=hit["line"],
                            cwe="CWE-327",
                            language=lang,
                        )
                        _add("SEC-WEAK-CRYPTO", f)
                        penalty += _PENALTY["SEC-WEAK-CRYPTO"]
                except Exception:
                    log.debug("security_engine: weak_crypto failed for %s", rel_path)

            # -- Dangerous Exec --
            if exec_fn:
                try:
                    for hit in exec_fn(tree, rel_path):
                        cwe = hit.get("cwe", "CWE-78")
                        sev = "High" if cwe == "CWE-78" else "High"
                        f = _make_finding(
                            rule_id="SEC-DANGEROUS-EXEC",
                            title=f"Dangerous Execution API: {hit['api']}",
                            description=hit["detail"],
                            severity=sev,
                            file=rel_path,
                            line=hit["line"],
                            cwe=cwe,
                            language=lang,
                        )
                        _add("SEC-DANGEROUS-EXEC", f)
                        penalty += _PENALTY["SEC-DANGEROUS-EXEC"]
                except Exception:
                    log.debug("security_engine: dangerous_exec failed for %s", rel_path)

            # -- Unsafe Assert --
            if assert_fn:
                try:
                    for hit in assert_fn(tree, rel_path):
                        f = _make_finding(
                            rule_id="SEC-UNSAFE-ASSERT",
                            title="Unsafe Assert as Security Check",
                            description=hit["detail"],
                            severity="Medium",
                            file=rel_path,
                            line=hit["line"],
                            cwe="CWE-617",
                            language=lang,
                        )
                        _add("SEC-UNSAFE-ASSERT", f)
                        penalty += _PENALTY["SEC-UNSAFE-ASSERT"]
                except Exception:
                    log.debug("security_engine: unsafe_assert failed for %s", rel_path)

            # -- CWE-703 Exception Handling --
            if exc_fn:
                try:
                    for hit in exc_fn(tree, rel_path):
                        f = _make_finding(
                            rule_id="SEC-CWE-703",
                            title=f"Missing Exception Handling: {hit['api']}",
                            description=hit["detail"],
                            severity="Medium",
                            file=rel_path,
                            line=hit["line"],
                            cwe="CWE-703",
                            language=lang,
                        )
                        _add("SEC-CWE-703", f)
                        penalty += _PENALTY["SEC-CWE-703"]
                except Exception:
                    log.debug("security_engine: exc_handling failed for %s", rel_path)

    penalty = min(penalty, _MAX_PENALTY)
    return findings, penalty
