"""
analysis/rules/smells/smell_engine.py — Phase 2 Code-Smell Engine.

Orchestrates all smell rules against a project directory and returns a list
of Finding dicts compatible with the existing analyze.py pipeline.

Rules implemented
-----------------
CODE-LONG-LINE              All 5 languages  (text scan)
CODE-UNDEFINED-NAME         Python, JS/TS    (AST scope analysis)
CODE-UNUSED-VARIABLE        Python, JS/TS    (AST body walk)
CODE-UNUSED-ARGUMENT        Python, JS/TS    (AST body walk)  [top-level fns only]
CODE-TOO-FEW-PUBLIC-METHODS All 5 languages  (reuses class_metrics)
CODE-INCONSISTENT-RETURN    Python, JS/TS    (AST return analysis)
CODE-FORMATTING             Python (mixed-indent), JS/TS/Java/C++ (brace-style)
CODE-DUPLICATE-BLOCK        All 5 languages  (AST structural fingerprint)

Integration with analyze.py
----------------------------
Call run_smell_engine(project_path) in event_generator() as a new Stage 8.
It returns (findings: list[dict], penalty: int) matching the existing contract.

Scoring / Penalty (added to structural_score)
----------------------------------------------
Each smell type contributes a small penalty:
  CODE-LONG-LINE              1 per file with offending lines  (max 5 per file)
  CODE-UNDEFINED-NAME         5 per name
  CODE-UNUSED-VARIABLE        2 per instance
  CODE-UNUSED-ARGUMENT        2 per instance
  CODE-TOO-FEW-PUBLIC-METHODS 3 per class
  CODE-INCONSISTENT-RETURN    4 per function
  CODE-FORMATTING             2 per file issue
  CODE-DUPLICATE-BLOCK        5 per duplicate pair

Total penalty is soft-capped at 30 to avoid overwhelming the score.
"""

from __future__ import annotations
import logging
import os

from analysis.finding import Finding
from analysis.rule_registry import get as get_rule
from analysis.parsing.ast_parser import parse_file
from analysis.parsing.language_config import LANGUAGE_CONFIG

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ignore paths
# ---------------------------------------------------------------------------
_IGNORED_DIRS = frozenset({
    "node_modules", "venv", ".venv", ".git", "__pycache__",
    "dist", "build", ".next", "out", "target",
})

# ---------------------------------------------------------------------------
# Penalty weights
# ---------------------------------------------------------------------------
_PENALTY = {
    "CODE-LONG-LINE":               1,
    "CODE-UNDEFINED-NAME":          5,
    "CODE-UNUSED-VARIABLE":         2,
    "CODE-UNUSED-ARGUMENT":         2,
    "CODE-TOO-FEW-PUBLIC-METHODS":  3,
    "CODE-INCONSISTENT-RETURN":     4,
    "CODE-FORMATTING":              2,
    "CODE-DUPLICATE-BLOCK":         5,
}
_MAX_PENALTY = 30


# ---------------------------------------------------------------------------
# Helper: language from filename
# ---------------------------------------------------------------------------
def _get_language(filename: str) -> str:
    for lang, config in LANGUAGE_CONFIG.items():
        if any(filename.endswith(ext) for ext in config["extensions"]):
            return lang
    return ""


def _read_lines(filepath: str) -> list[str]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            return fh.readlines()
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Finding factory
# ---------------------------------------------------------------------------
def _make_finding(rule_id: str, title: str, description: str, severity: str,
                  file: str = "", line: int = 1, **_extra) -> dict:
    spec = get_rule(rule_id)
    return Finding(
        rule_id=rule_id,
        category="Code Smell",
        title=title,
        description=description,
        severity=severity,
        rule=spec.name if spec else rule_id,
        resolution=spec.resolution if spec else None,
        file=file or None,
        line=line or None,
    ).to_dict()


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_smell_engine(project_path: str) -> tuple[list[dict], int]:
    """Run all smell rules on *project_path*.

    Returns (findings: list[dict], penalty: int).
    """
    from .line_length import check_line_length
    from .undefined_names import (
        analyze_python_undef, analyze_js_undef,
        analyze_java_undef, analyze_cpp_undef,
    )
    from .unused_symbols import (
        analyze_python_unused, analyze_js_unused,
        analyze_java_unused, analyze_cpp_unused,
    )
    from .public_methods import check_too_few_public_methods
    from .returns import (
        analyze_python_returns, analyze_js_returns,
        analyze_java_returns, analyze_cpp_returns,
    )
    from .formatting import check_formatting
    from .duplicate_code import extract_function_bodies, find_duplicates
    from analysis.metrics.class_metrics import compute_class_metrics

    findings: list[dict] = []
    penalty = 0

    # Per-file processing
    all_function_bodies: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if d not in _IGNORED_DIRS]

        for fname in filenames:
            lang = _get_language(fname)
            if not lang:
                continue

            filepath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(filepath, project_path)

            lines = _read_lines(filepath)
            tree = None
            try:
                tree = parse_file(filepath, lang)
            except Exception:
                log.debug("smell_engine: parse failed for %s", filepath)

            # ----------------------------------------------------------------
            # CODE-LONG-LINE  (all languages, text-only)
            # ----------------------------------------------------------------
            try:
                ll_hits = check_line_length(lines, rel_path)
                if ll_hits:
                    # Emit one finding per first offending line (cap 3 per file)
                    for hit in ll_hits[:3]:
                        f = _make_finding(
                            rule_id="CODE-LONG-LINE",
                            title="Long Line",
                            description=(
                                f"Line {hit['line_no']} is {hit['length']} characters "
                                f"(threshold: {hit['threshold']}). "
                                f"Snippet: {hit['snippet']}"
                            ),
                            severity="Low",
                            file=rel_path,
                            line=hit["line_no"],
                        )
                        findings.append(f)
                    penalty += _PENALTY["CODE-LONG-LINE"] * min(len(ll_hits), 5)
            except Exception:
                log.debug("smell_engine: line_length failed for %s", rel_path)

            if tree is None:
                continue

            # ----------------------------------------------------------------
            # CODE-UNDEFINED-NAME
            # ----------------------------------------------------------------
            try:
                undef_fn = {
                    "Python": analyze_python_undef,
                    "JavaScript": analyze_js_undef,
                    "TypeScript": analyze_js_undef,
                    "Java": analyze_java_undef,
                    "C++": analyze_cpp_undef,
                }.get(lang)
                if undef_fn:
                    for hit in undef_fn(tree, rel_path):
                        f = _make_finding(
                            rule_id="CODE-UNDEFINED-NAME",
                            title=f"Undefined Name: {hit['name']}",
                            description=(
                                f"Reference to '{hit['name']}' at line {hit['line']} "
                                "has no visible declaration in this file's scope. "
                                "May be a typo or missing import."
                            ),
                            severity="Medium",
                            file=rel_path,
                            line=hit["line"],
                        )
                        findings.append(f)
                        penalty += _PENALTY["CODE-UNDEFINED-NAME"]
            except Exception:
                log.debug("smell_engine: undefined_names failed for %s", rel_path)

            # ----------------------------------------------------------------
            # CODE-UNUSED-VARIABLE / CODE-UNUSED-ARGUMENT
            # ----------------------------------------------------------------
            try:
                unused_fn = {
                    "Python": analyze_python_unused,
                    "JavaScript": analyze_js_unused,
                    "TypeScript": analyze_js_unused,
                    "Java": analyze_java_unused,
                    "C++": analyze_cpp_unused,
                }.get(lang)
                if unused_fn:
                    for hit in unused_fn(tree, rel_path):
                        rid = hit["rule_id"]
                        if rid == "CODE-UNUSED-VARIABLE":
                            name = hit.get("var", "?")
                            title = f"Unused Variable: {name}"
                            desc = (
                                f"Variable '{name}' is declared at line {hit['line']} "
                                "but never referenced in its scope."
                            )
                        else:
                            name = hit.get("param", "?")
                            title = f"Unused Argument: {name}"
                            desc = (
                                f"Parameter '{name}' at line {hit['line']} "
                                "is never used inside the function body."
                            )
                        f = _make_finding(
                            rule_id=rid,
                            title=title,
                            description=desc,
                            severity="Low",
                            file=rel_path,
                            line=hit["line"],
                        )
                        findings.append(f)
                        penalty += _PENALTY.get(rid, 2)
            except Exception:
                log.debug("smell_engine: unused_symbols failed for %s", rel_path)

            # ----------------------------------------------------------------
            # CODE-INCONSISTENT-RETURN
            # ----------------------------------------------------------------
            try:
                ret_fn = {
                    "Python": analyze_python_returns,
                    "JavaScript": analyze_js_returns,
                    "TypeScript": analyze_js_returns,
                    "Java": analyze_java_returns,
                    "C++": analyze_cpp_returns,
                }.get(lang)
                if ret_fn:
                    for hit in ret_fn(tree, rel_path):
                        f = _make_finding(
                            rule_id="CODE-INCONSISTENT-RETURN",
                            title=f"Inconsistent Return in '{hit['func']}'",
                            description=(
                                f"Function '{hit['func']}' has {hit['valued_count']} "
                                f"return-with-value and {hit['bare_count']} bare/empty "
                                "return statements. Some code paths do not return a value."
                            ),
                            severity="Medium",
                            file=rel_path,
                            line=hit["line"],
                        )
                        findings.append(f)
                        penalty += _PENALTY["CODE-INCONSISTENT-RETURN"]
            except Exception:
                log.debug("smell_engine: returns failed for %s", rel_path)

            # ----------------------------------------------------------------
            # CODE-FORMATTING
            # ----------------------------------------------------------------
            try:
                for hit in check_formatting(lines, rel_path):
                    f = _make_finding(
                        rule_id="CODE-FORMATTING",
                        title="Formatting Anomaly",
                        description=hit["detail"],
                        severity="Low",
                        file=rel_path,
                        line=hit["line"],
                    )
                    findings.append(f)
                    penalty += _PENALTY["CODE-FORMATTING"]
            except Exception:
                log.debug("smell_engine: formatting failed for %s", rel_path)

            # ----------------------------------------------------------------
            # CODE-TOO-FEW-PUBLIC-METHODS (collect class metrics per file)
            # ----------------------------------------------------------------
            try:
                cls_metrics = compute_class_metrics(tree, lang, rel_path)
                for hit in check_too_few_public_methods(cls_metrics):
                    f = _make_finding(
                        rule_id="CODE-TOO-FEW-PUBLIC-METHODS",
                        title=f"Too Few Public Methods in '{hit['class_name']}'",
                        description=(
                            f"Class '{hit['class_name']}' has {hit['public_methods']} "
                            f"public method(s); the configured minimum is {hit['min_methods']}. "
                            "Consider promoting this to a function or adding a second method."
                        ),
                        severity="Low",
                        file=rel_path,
                        line=hit["line"],
                    )
                    findings.append(f)
                    penalty += _PENALTY["CODE-TOO-FEW-PUBLIC-METHODS"]
            except Exception:
                log.debug("smell_engine: public_methods failed for %s", rel_path)

            # ----------------------------------------------------------------
            # Collect bodies for duplicate detection (done after all files)
            # ----------------------------------------------------------------
            try:
                from .duplicate_code import extract_function_bodies
                bodies = extract_function_bodies(tree, rel_path)
                all_function_bodies.extend(bodies)
            except Exception:
                log.debug("smell_engine: body extraction failed for %s", rel_path)

    # ------------------------------------------------------------------------
    # CODE-DUPLICATE-BLOCK  (cross-file, done after walking all files)
    # ------------------------------------------------------------------------
    try:
        from .duplicate_code import find_duplicates
        for hit in find_duplicates(all_function_bodies):
            secondary_info = (
                f"Also found as '{hit['secondary_func']}' in "
                f"{hit['secondary_file']} at line {hit['secondary_line']}."
            )
            f = _make_finding(
                rule_id="CODE-DUPLICATE-BLOCK",
                title=(
                    f"Duplicate Code Block: '{hit['primary_func']}' "
                    f"and '{hit['secondary_func']}'"
                ),
                description=(
                    f"Function '{hit['primary_func']}' ({hit['primary_file']}:"
                    f"{hit['primary_line']}) has the same structural fingerprint as "
                    f"'{hit['secondary_func']}' ({hit['secondary_file']}:"
                    f"{hit['secondary_line']}). "
                    f"({hit['token_count']} structural tokens matched.) "
                    f"{secondary_info}"
                ),
                severity="Medium",
                file=hit["primary_file"],
                line=hit["primary_line"],
            )
            findings.append(f)
            penalty += _PENALTY["CODE-DUPLICATE-BLOCK"]
    except Exception:
        log.debug("smell_engine: duplicate_code failed")

    penalty = min(penalty, _MAX_PENALTY)
    return findings, penalty
