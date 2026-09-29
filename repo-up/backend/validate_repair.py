"""
validate_repair.py — Phase 5 repair engine tests.

Run from backend/: python validate_repair.py

Tests per deterministic repair
-------------------------------
1. Valid vulnerable source → patch generated
2. Expected old_text matches → validates correctly
3. Patched source is different from original
4. Patched source parses without errors (Tree-sitter check)
5. Original source is unchanged
6. Mismatched old_text → patch rejected (validation error)
7. Path escape → rejected
8. Tier 2 / Tier 3 → no patch, explanation returned
9. All existing tests (validate.py, validate_smells.py, validate_security.py) pass
"""

import os
import sys
import subprocess
import tempfile
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.repair.repair_engine import get_candidate_patch
from analysis.repair.patch_model import (
    Patch, validate_patch, PatchValidationError,
    apply_patch_to_string, TIER_1, TIER_2, TIER_3,
)


def _pass(msg):
    print(f"  PASS  {msg}")


def _fail(msg):
    print(f"  FAIL  {msg}")
    sys.exit(1)


def _info(msg):
    print(f"  INFO  {msg}")


# ---------------------------------------------------------------------------
# Helper: write a temp file and get its real path
# ---------------------------------------------------------------------------
def _write_temp(content: str, suffix: str, tmpdir: str) -> str:
    path = os.path.join(tmpdir, f"test{suffix}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def main():
    print("=" * 65)
    print("validate_repair.py — Phase 5 Repair Engine Tests")
    print("=" * 65)

    passed = 0
    tmpdir = tempfile.mkdtemp()

    try:
        # ================================================================
        # PYTHON: yaml.load → yaml.safe_load (SEC-CWE-502)
        # ================================================================
        print("\n--- Python: yaml.load -> yaml.safe_load (SEC-CWE-502) ---")

        py_source = (
            "import yaml\n"
            "\n"
            "def load_config(stream):\n"
            "    return yaml.load(stream)\n"   # vulnerable line 4
        )
        py_file = _write_temp(py_source, ".py", tmpdir)
        rel_file = os.path.relpath(py_file, tmpdir)

        finding = {
            "rule_id": "SEC-CWE-502",
            "language": "Python",
            "file": rel_file,
            "line": 4,
            "title": "Unsafe Deserialization: yaml.load",
            "description": "yaml.load without SafeLoader",
            "severity": "High",
            "category": "Security",
        }

        # Test 1: patch generated
        print("\nTest 1: Patch generated for yaml.load")
        resp = get_candidate_patch(finding, tmpdir)
        if resp.patch is None:
            _fail(f"Expected a patch, got None. Error: {resp.validation_error}")
        else:
            _pass(f"Patch generated: {resp.patch.description[:60]}")
            passed += 1

        # Test 2: old_text matches
        print("\nTest 2: old_text matches source line")
        if resp.patch:
            with open(py_file) as f:
                lines = f.readlines()
            actual_line = lines[finding["line"] - 1]
            if resp.patch.old_text != actual_line:
                _fail(f"old_text mismatch:\n  expected: {actual_line!r}\n  got:      {resp.patch.old_text!r}")
            else:
                _pass("old_text matches source line exactly")
                passed += 1

        # Test 3: Patched source differs from original
        print("\nTest 3: Patched source is different from original")
        if resp.patch:
            patched = apply_patch_to_string(py_source, resp.patch)
            if patched == py_source:
                _fail("Patch produced no change")
            elif "yaml.safe_load" in patched and "yaml.load(" not in patched.replace("yaml.safe_load", ""):
                _pass("Patched source contains yaml.safe_load, no bare yaml.load")
                passed += 1
            else:
                _fail(f"Unexpected patched source:\n{patched}")

        # Test 4: Patched source parses
        print("\nTest 4: Patched source parses via Tree-sitter")
        if resp.patch:
            patched = apply_patch_to_string(py_source, resp.patch)
            try:
                from analysis.parsing.ast_parser import LANGUAGES, Parser
                if "Python" in LANGUAGES:
                    parser = Parser(LANGUAGES["Python"])
                    tree = parser.parse(bytes(patched, "utf-8"))
                    if tree.root_node.has_error:
                        _fail("Patched Python source has parse errors")
                    else:
                        _pass("Patched source parses cleanly")
                        passed += 1
                else:
                    print("  SKIP  Python grammar not available")
            except Exception as exc:
                _fail(f"Parse check raised: {exc}")

        # Test 5: Original file unchanged
        print("\nTest 5: Original file unchanged")
        with open(py_file) as f:
            original_on_disk = f.read()
        if original_on_disk != py_source:
            _fail("ORIGINAL FILE WAS MODIFIED!")
        else:
            _pass("Original file is unchanged on disk")
            passed += 1

        # Test 6: Mismatched old_text → rejected
        print("\nTest 6: Invalid patch (wrong old_text) rejected by validate_patch")
        with open(py_file) as f:
            lines = f.readlines()
        bad_patch = Patch(
            rule_id="SEC-CWE-502",
            language="Python",
            tier=TIER_1,
            file=rel_file,
            start_line=4,
            start_col=0,
            end_line=4,
            end_col=len(lines[3]),
            old_text="WRONG TEXT THAT DOES NOT EXIST IN FILE\n",
            new_text="    return yaml.safe_load(stream)\n",
            description="test",
        )
        try:
            validate_patch(bad_patch, tmpdir, lines)
            _fail("Expected PatchValidationError but none raised")
        except PatchValidationError as exc:
            _pass(f"Correctly rejected: {exc}")
            passed += 1

        # Test 7: Path escape rejected
        print("\nTest 7: Path escape rejected")
        escaped_patch = Patch(
            rule_id="SEC-CWE-502",
            language="Python",
            tier=TIER_1,
            file="../../etc/passwd",
            start_line=1,
            start_col=0,
            end_line=1,
            end_col=4,
            old_text="root",
            new_text="yaml.safe_load",
            description="test",
        )
        try:
            validate_patch(escaped_patch, tmpdir, ["root:x:0:0\n"])
            _fail("Expected PatchValidationError for path escape")
        except PatchValidationError as exc:
            _pass(f"Path escape correctly rejected: {exc}")
            passed += 1

        # ================================================================
        # PYTHON: hashlib.md5 → hashlib.sha256 (SEC-WEAK-CRYPTO)
        # ================================================================
        print("\n--- Python: hashlib.md5 -> hashlib.sha256 (SEC-WEAK-CRYPTO) ---")

        py_crypto = (
            "import hashlib\n"
            "\n"
            "def hash_it(data):\n"
            "    return hashlib.md5(data).hexdigest()\n"   # line 4
        )
        py_crypto_file = _write_temp(py_crypto, "_crypto.py", tmpdir)
        rel_crypto = os.path.relpath(py_crypto_file, tmpdir)

        crypto_finding = {
            "rule_id": "SEC-WEAK-CRYPTO",
            "language": "Python",
            "file": rel_crypto,
            "line": 4,
            "title": "Weak Cryptographic Hash: MD5",
            "description": "hashlib.md5 is weak",
            "severity": "Medium",
            "category": "Security",
        }

        print("\nTest 8: Python md5 -> sha256 patch generated")
        resp2 = get_candidate_patch(crypto_finding, tmpdir)
        if resp2.patch is None:
            _fail(f"Expected patch, got None. Error: {resp2.validation_error}")
        elif "sha256" not in resp2.patch.new_text:
            _fail(f"Expected sha256 in new_text, got: {resp2.patch.new_text!r}")
        else:
            _pass(f"sha256 patch generated correctly")
            passed += 1

        print("\nTest 9: Patched Python crypto source unchanged on disk")
        with open(py_crypto_file) as f:
            still_original = f.read()
        if still_original != py_crypto:
            _fail("Original crypto file was modified!")
        else:
            _pass("Original crypto file unchanged")
            passed += 1

        # ================================================================
        # JAVASCRIPT: createHash('md5') → createHash('sha256')
        # ================================================================
        print("\n--- JavaScript: createHash md5 -> sha256 (SEC-WEAK-CRYPTO) ---")

        js_source = (
            "const crypto = require('crypto');\n"
            "\n"
            "function hashIt(data) {\n"
            "    return crypto.createHash('md5').update(data).digest('hex');\n"  # line 4
            "}\n"
        )
        js_file = _write_temp(js_source, ".js", tmpdir)
        rel_js = os.path.relpath(js_file, tmpdir)

        js_finding = {
            "rule_id": "SEC-WEAK-CRYPTO",
            "language": "JavaScript",
            "file": rel_js,
            "line": 4,
            "title": "Weak Cryptographic Hash: MD5",
            "description": "createHash md5",
            "severity": "Medium",
            "category": "Security",
        }

        print("\nTest 10: JS createHash md5 -> sha256 patch generated")
        resp3 = get_candidate_patch(js_finding, tmpdir)
        if resp3.patch is None:
            _fail(f"Expected JS patch, got None. Error: {resp3.validation_error}")
        elif "sha256" not in resp3.patch.new_text:
            _fail(f"Expected sha256, got: {resp3.patch.new_text!r}")
        else:
            _pass("JS md5->sha256 patch generated")
            passed += 1

        # ================================================================
        # JAVA: getInstance("MD5") → getInstance("SHA-256")
        # ================================================================
        print("\n--- Java: getInstance(MD5) -> getInstance(SHA-256) (SEC-WEAK-CRYPTO) ---")

        java_source = (
            "import java.security.MessageDigest;\n"
            "public class Crypto {\n"
            "    public String hash(String data) throws Exception {\n"
            "        MessageDigest md = MessageDigest.getInstance(\"MD5\");\n"  # line 4
            "        return new String(md.digest(data.getBytes()));\n"
            "    }\n"
            "}\n"
        )
        java_file = _write_temp(java_source, ".java", tmpdir)
        rel_java = os.path.relpath(java_file, tmpdir)

        java_finding = {
            "rule_id": "SEC-WEAK-CRYPTO",
            "language": "Java",
            "file": rel_java,
            "line": 4,
            "title": "Weak Cryptographic Hash: MD5",
            "description": "getInstance MD5",
            "severity": "Medium",
            "category": "Security",
        }

        print("\nTest 11: Java getInstance MD5 -> SHA-256 patch generated")
        resp4 = get_candidate_patch(java_finding, tmpdir)
        if resp4.patch is None:
            _fail(f"Expected Java patch, got None. Error: {resp4.validation_error}")
        elif "SHA-256" not in resp4.patch.new_text:
            _fail(f"Expected SHA-256, got: {resp4.patch.new_text!r}")
        else:
            _pass("Java MD5->SHA-256 patch generated")
            passed += 1

        # ================================================================
        # Tier 2: SEC-DANGEROUS-EXEC Python → no patch, has explanation
        # ================================================================
        print("\n--- Tier 2: SEC-DANGEROUS-EXEC Python -> explanation only ---")

        tier2_finding = {
            "rule_id": "SEC-DANGEROUS-EXEC",
            "language": "Python",
            "file": rel_file,
            "line": 1,
            "title": "Dangerous exec",
            "description": "os.system",
            "severity": "High",
            "category": "Security",
        }

        print("\nTest 12: Tier 2 returns explanation, no patch")
        resp5 = get_candidate_patch(tier2_finding, tmpdir)
        if resp5.patch is not None:
            _fail("Tier 2 should not return a patch")
        elif resp5.tier != TIER_2:
            _fail(f"Expected TIER_2, got {resp5.tier}")
        elif not resp5.explanation:
            _fail("Tier 2 should return an explanation")
        else:
            _pass(f"Tier 2: no patch, explanation='{resp5.explanation[:60]}'")
            passed += 1

        # ================================================================
        # Tier 3: SEC-UNSAFE-ASSERT → explanation only
        # ================================================================
        print("\n--- Tier 3: SEC-UNSAFE-ASSERT -> explanation only ---")

        tier3_finding = {
            "rule_id": "SEC-UNSAFE-ASSERT",
            "language": "Python",
            "file": rel_file,
            "line": 1,
            "title": "Unsafe Assert",
            "description": "assert used for auth",
            "severity": "Medium",
            "category": "Security",
        }

        print("\nTest 13: Tier 3 returns explanation, no patch")
        resp6 = get_candidate_patch(tier3_finding, tmpdir)
        if resp6.patch is not None:
            _fail("Tier 3 should not return a patch")
        elif resp6.tier != TIER_3:
            _fail(f"Expected TIER_3, got {resp6.tier}")
        elif not resp6.explanation:
            _fail("Tier 3 should return an explanation")
        else:
            _pass(f"Tier 3: no patch, explanation='{resp6.explanation[:60]}'")
            passed += 1

        # ================================================================
        # Unknown rule → repair_available=False
        # ================================================================
        print("\n--- Unknown rule -> repair_available=False ---")

        print("\nTest 14: Unknown rule returns repair_available=False")
        resp7 = get_candidate_patch(
            {"rule_id": "UNKNOWN-RULE-XYZ", "language": "Python", "file": rel_file, "line": 1,
             "title": "", "description": "", "severity": "Low", "category": ""},
            tmpdir,
        )
        if resp7.repair_available:
            _fail("Unknown rule should have repair_available=False")
        else:
            _pass("Unknown rule: repair_available=False")
            passed += 1

        # ================================================================
        # Diff output check
        # ================================================================
        print("\n--- Unified diff output ---")
        print("\nTest 15: Diff is non-empty for Tier 1 patch")
        resp8 = get_candidate_patch(finding, tmpdir)
        if resp8.patch and resp8.patch.unified_diff():
            _pass(f"Diff generated:\n{resp8.patch.unified_diff()[:200]}")
            passed += 1
        else:
            _fail("Empty diff for Tier 1 patch")

        # ================================================================
        # Existing test suites
        # ================================================================
        print("\n--- Existing test suites ---")
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
                print(result.stdout[-300:])
                _fail(f"{script} failed")
            else:
                passed += 1

        print(f"\n{'=' * 65}")
        print(f"REPAIR TESTS: {passed} checks passed")
        print(f"{'=' * 65}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
