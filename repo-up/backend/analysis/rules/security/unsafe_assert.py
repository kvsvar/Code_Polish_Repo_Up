"""
analysis/rules/security/unsafe_assert.py
SEC-UNSAFE-ASSERT — Assert Used as a Security Boundary

Python's assert statements are stripped in optimized mode (-O / -OO).
Using assert for security checks (authentication, authorization, input
validation) therefore creates a silently-disabled security gate.

Approach
--------
NOT every assert is reported — only those that appear to guard a security
boundary. We use a keyword-based heuristic on the test expression:

High-confidence security keywords (direct string match in assertion text):
  auth, login, admin, permission, privilege, role, token, session,
  password, credential, secret, access, authorized, authenticated

If the assert's test expression mentions one of these words, it is flagged.

Limitations
-----------
* This is a HEURISTIC. It will produce false positives for:
  - assert statements in test suites (where "auth" appears in test names)
  - developer-intent assertions that happen to use these words
* We skip assertions inside test_*.py files and conftest.py to reduce FP.
* We do NOT skip all class methods — only explicit test file names.

Supported: Python only
Java/JS/TS/C++: assert in these languages is either disabled differently
  or serves a well-understood role. We document this as out of scope.

CWE mapping
-----------
CWE-617: Reachable Assertion (close analogue — assert causing DoS or bypass)
This is an approximate mapping. We document this clearly.
"""

from __future__ import annotations
import os
from analysis.rules.smells.ast_helpers import walk_depth_first, node_text

# Keywords that suggest an assertion is guarding a security property
_SECURITY_KEYWORDS = frozenset({
    "auth", "login", "admin", "permission", "privilege", "role",
    "token", "session", "password", "credential", "secret",
    "access", "authorized", "authenticated", "root", "superuser",
    "acl", "ownership", "owner", "verified", "validate", "user_id",
})

_TEST_FILE_PATTERNS = ("test_", "_test.py", "conftest.py", "spec_", "_spec.py")


def _is_test_file(rel_path: str) -> bool:
    base = os.path.basename(rel_path).lower()
    return any(base.startswith(p) or base.endswith(p) for p in _TEST_FILE_PATTERNS)


def _contains_security_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in _SECURITY_KEYWORDS)


def analyze_python_unsafe_assert(tree, rel_path: str) -> list[dict]:
    """Return SEC-UNSAFE-ASSERT findings for Python files."""
    if _is_test_file(rel_path):
        return []

    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "assert_statement":
            continue

        # assert_statement children: "assert", test_expr, optional message
        test_node = None
        for child in node.children:
            if child.type not in ("assert", ","):
                test_node = child
                break

        if test_node is None:
            continue

        test_text = node_text(test_node)
        if _contains_security_keyword(test_text):
            results.append({
                "rule_id": "SEC-UNSAFE-ASSERT",
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "test_expr": test_text[:120],
                "detail": (
                    f"assert statement appears to guard a security check "
                    f"(expression: `{test_text[:80]}`). "
                    "Python asserts are disabled in optimized mode (`python -O`), "
                    "making this check silently bypassable. "
                    "Use an explicit conditional and raise an appropriate exception instead."
                ),
            })

    return results
