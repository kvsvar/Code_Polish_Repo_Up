"""
validate_parity.py — Phase 4 Cross-Language Parity Test.

Run from backend/: python validate_parity.py

Outputs a structured report of:
  - Files parsed per language
  - AST parse success rate
  - Findings per rule
  - Rules triggered per language
  - Parse failures
  - Scoring determinism (run twice, expect same output)
  - Empty-repo safety (no crash / no div-by-zero)
  - Bounded score [0-100]
"""

import os
import sys
import json
import collections

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.parsing.ast_parser import parse_file, LANGUAGES
from analysis.parsing.language_config import LANGUAGE_CONFIG
from analysis.rules.smells.smell_engine import run_smell_engine
from analysis.rules.security.security_engine import run_security_engine
from analysis.metrics.class_metrics import calculate_repo_averages
from analysis.scorer import compute_repo_score
from analysis.cross_language.capability_matrix import CAPABILITY_MATRIX, render_matrix_table

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "test_fixtures", "fixture_cross_lang")

LANGS = {
    "python":     "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java":       "Java",
    "cpp":        "C++",
}


def _pass(msg):
    print(f"  PASS  {msg}")


def _fail(msg):
    print(f"  FAIL  {msg}")
    sys.exit(1)


def _info(msg):
    print(f"  INFO  {msg}")


def parse_stats(lang_dir: str, lang: str) -> dict:
    """Walk a fixture directory and collect parse statistics."""
    stats = {
        "language":      lang,
        "files_found":   0,
        "ast_success":   0,
        "ast_fail":      0,
        "parse_errors":  [],
    }
    if not os.path.isdir(lang_dir):
        return stats

    config = LANGUAGE_CONFIG.get(lang, {})
    exts = set(config.get("extensions", []))

    for fname in os.listdir(lang_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in exts:
            continue
        stats["files_found"] += 1
        filepath = os.path.join(lang_dir, fname)
        tree = parse_file(filepath, lang)
        if tree is not None:
            stats["ast_success"] += 1
        else:
            stats["ast_fail"] += 1
            stats["parse_errors"].append(fname)

    return stats


def findings_by_rule(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = collections.defaultdict(int)
    for f in findings:
        counts[f.get("rule_id", "UNKNOWN")] += 1
    return dict(sorted(counts.items()))


def main():
    print("=" * 70)
    print("validate_parity.py — Phase 4 Cross-Language Parity Report")
    print("=" * 70)

    all_passed = True

    # ----------------------------------------------------------------
    # 1. Capability Matrix
    # ----------------------------------------------------------------
    print("\n--- CAPABILITY MATRIX ---")
    print(render_matrix_table())

    # ----------------------------------------------------------------
    # 2. AST Parse stats per language
    # ----------------------------------------------------------------
    print("\n--- AST PARSE STATS ---")
    parse_report = {}
    for subdir, lang in LANGS.items():
        lang_dir = os.path.join(FIXTURE_DIR, subdir)
        stats = parse_stats(lang_dir, lang)
        parse_report[lang] = stats
        total = stats["files_found"]
        ok = stats["ast_success"]
        fail = stats["ast_fail"]
        status = "OK" if total > 0 and fail == 0 else ("WARN" if total > 0 else "SKIP")
        print(f"  {lang:<15} files={total}  parsed={ok}  failed={fail}  [{status}]")
        if stats["parse_errors"]:
            for e in stats["parse_errors"]:
                print(f"             PARSE FAIL: {e}")

    # ----------------------------------------------------------------
    # 3. Smell engine per language subdir
    # ----------------------------------------------------------------
    print("\n--- CODE SMELL FINDINGS PER LANGUAGE ---")
    smell_report = {}
    for subdir, lang in LANGS.items():
        lang_dir = os.path.join(FIXTURE_DIR, subdir)
        if not os.path.isdir(lang_dir):
            print(f"  {lang:<15} SKIP (fixture dir not found)")
            continue
        findings, penalty = run_smell_engine(lang_dir)
        by_rule = findings_by_rule(findings)
        smell_report[lang] = {"count": len(findings), "by_rule": by_rule, "penalty": penalty}
        print(f"  {lang:<15} findings={len(findings)}  penalty={penalty}")
        for rule_id, count in by_rule.items():
            print(f"             {rule_id}: {count}")

    # ----------------------------------------------------------------
    # 4. Security engine per language subdir
    # ----------------------------------------------------------------
    print("\n--- SECURITY FINDINGS PER LANGUAGE ---")
    sec_report = {}
    for subdir, lang in LANGS.items():
        lang_dir = os.path.join(FIXTURE_DIR, subdir)
        if not os.path.isdir(lang_dir):
            print(f"  {lang:<15} SKIP (fixture dir not found)")
            continue
        findings, penalty = run_security_engine(lang_dir)
        by_rule = findings_by_rule(findings)
        sec_report[lang] = {"count": len(findings), "by_rule": by_rule, "penalty": penalty}
        print(f"  {lang:<15} findings={len(findings)}  penalty={penalty}")
        for rule_id, count in by_rule.items():
            print(f"             {rule_id}: {count}")

    # ----------------------------------------------------------------
    # 5. Scoring determinism + bounds check
    # ----------------------------------------------------------------
    print("\n--- SCORING DETERMINISM & BOUNDS ---")
    for subdir, lang in LANGS.items():
        lang_dir = os.path.join(FIXTURE_DIR, subdir)
        if not os.path.isdir(lang_dir):
            continue
        try:
            averages, _ = calculate_repo_averages(lang_dir)
            score1 = compute_repo_score(averages, structural_score=80, security_score=80)
            score2 = compute_repo_score(averages, structural_score=80, security_score=80)

            final1 = score1["final_score"]
            final2 = score2["final_score"]

            if final1 != final2:
                print(f"  {lang:<15} FAIL: non-deterministic ({final1} vs {final2})")
                all_passed = False
            elif not (0 <= final1 <= 100):
                print(f"  {lang:<15} FAIL: score out of bounds ({final1})")
                all_passed = False
            else:
                print(f"  {lang:<15} score={final1}  deterministic=YES  in-bounds=YES")
        except Exception as exc:
            print(f"  {lang:<15} ERROR: {exc}")
            all_passed = False

    # ----------------------------------------------------------------
    # 6. Empty-repo safety
    # ----------------------------------------------------------------
    print("\n--- EMPTY REPO SAFETY ---")
    import shutil, tempfile
    tmp = tempfile.mkdtemp()
    try:
        averages, findings = calculate_repo_averages(tmp)
        score = compute_repo_score(averages, structural_score=100, security_score=100)
        final = score["final_score"]
        if not (0 <= final <= 100):
            print(f"  Empty repo: FAIL score={final}")
            all_passed = False
        else:
            print(f"  Empty repo: score={final}  no crash  no div-by-zero")
    except Exception as exc:
        print(f"  Empty repo: EXCEPTION {exc}")
        all_passed = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ----------------------------------------------------------------
    # 7. Line-number accuracy spot check
    # ----------------------------------------------------------------
    print("\n--- SOURCE LOCATION ACCURACY ---")
    py_dir = os.path.join(FIXTURE_DIR, "python")
    if os.path.isdir(py_dir):
        smell_findings, _ = run_smell_engine(py_dir)
        sec_findings, _ = run_security_engine(py_dir)
        all_findings = smell_findings + sec_findings
        no_line = [f for f in all_findings if f.get("line") is None]
        with_line = [f for f in all_findings if f.get("line") is not None]
        print(f"  Python: {len(with_line)} findings WITH line, {len(no_line)} WITHOUT line")
        if no_line:
            for f in no_line[:3]:
                print(f"    Missing line: {f.get('rule_id')} — {f.get('title')}")
    else:
        print("  Python fixture dir not found")

    # ----------------------------------------------------------------
    # 8. Existing tests
    # ----------------------------------------------------------------
    print("\n--- EXISTING TEST SUITES ---")
    import subprocess
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    for script in ("validate.py", "validate_smells.py", "validate_security.py"):
        result = subprocess.run(
            [sys.executable, script],
            cwd=backend_dir,
            capture_output=True, text=True,
        )
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"  {script:<30} {status}")
        if result.returncode != 0:
            print(result.stdout[-500:])
            all_passed = False

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\n" + "=" * 70)
    if all_passed:
        print("PARITY REPORT: ALL CHECKS PASSED")
    else:
        print("PARITY REPORT: SOME CHECKS FAILED — review above")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
