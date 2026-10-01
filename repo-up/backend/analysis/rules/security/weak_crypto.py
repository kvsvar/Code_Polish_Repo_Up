"""
analysis/rules/security/weak_crypto.py
SEC-WEAK-CRYPTO — Weak Cryptographic Hash Function Usage

CWE-327: Use of a Broken or Risky Cryptographic Algorithm
CWE-328: Use of Weak Hash  (specific hash sub-category)

We use CWE-327 (the broader, documented parent) for weak hash detection.

Approach
--------
Detect ACTUAL API calls to MD5/SHA-1, NOT arbitrary text.

Python:
  hashlib.md5()
  hashlib.sha1()
  hashlib.new("md5")  / hashlib.new("sha1")

Java:
  MessageDigest.getInstance("MD5")
  MessageDigest.getInstance("SHA-1") / ("SHA1")

JavaScript/TypeScript:
  crypto.createHash("md5")
  crypto.createHash("sha1") / ("sha-1")
  require('crypto').createHash(...)

C++:
  EVP_md5()   (OpenSSL)
  MD5_Init / MD5_Update / MD5_Final
  SHA1_Init / SHA1_Update / SHA1_Final
  (only the direct function-name pattern; full OpenSSL AST resolution is limited)

Limitations
-----------
* Weak hashes used for NON-SECURITY purposes (checksums, cache keys) are still
  flagged — we cannot determine intent via AST alone. The resolution text
  explains this nuance.
* MD5 in comments or string literals NOT part of API calls is NOT flagged.
"""

from __future__ import annotations
from analysis.rules.smells.ast_helpers import walk_depth_first, node_text, find_all

_WEAK_HASHES = frozenset({"md5", "sha1", "sha-1", "sha_1"})

# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

def _is_weak_hash_str(s: str) -> bool:
    return s.lower().strip("'\"") in _WEAK_HASHES


def analyze_python_weak_crypto(tree, rel_path: str) -> list[dict]:
    """Detect weak hash usage in Python via hashlib API calls."""
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "call":
            continue
        func = node.children[0] if node.children else None
        if func is None:
            continue
        func_text = node_text(func)

        # hashlib.md5() / hashlib.sha1()
        if func_text in ("hashlib.md5", "hashlib.sha1",
                         "md5", "sha1"):  # direct import
            algo = func_text.split(".")[-1]
            results.append({
                "rule_id": "SEC-WEAK-CRYPTO",
                "api": func_text + "()",
                "algo": algo.upper(),
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    f"Use of weak hash function `{func_text}()`. "
                    f"{algo.upper()} is cryptographically broken. "
                    "Use SHA-256 or SHA-3 for security-sensitive hashing."
                ),
            })
            continue

        if func_text in ("hashlib.new", "new"):
            args = [c for c in node.children if c.type == "argument_list"]
            if args:
                for arg_node in args[0].children:
                    if arg_node.type == "string" and _is_weak_hash_str(node_text(arg_node)):
                        algo = node_text(arg_node).strip("'\"")
                        results.append({
                            "rule_id": "SEC-WEAK-CRYPTO",
                            "api": f"hashlib.new({node_text(arg_node)})",
                            "algo": algo.upper(),
                            "line": node.start_point[0] + 1,
                            "file": rel_path,
                            "detail": (
                                f"hashlib.new() called with weak algorithm '{algo}'. "
                                "Use 'sha256' or 'sha3_256' instead."
                            ),
                        })

    return results


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

def analyze_java_weak_crypto(tree, rel_path: str) -> list[dict]:
    """Detect MessageDigest.getInstance(\"MD5\") in Java."""
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "method_invocation":
            continue

        children_texts = [node_text(c) for c in node.children]
        if "getInstance" not in children_texts:
            continue

        # Check arguments for weak algorithm name
        arg_list = next((c for c in node.children if c.type == "argument_list"), None)
        if arg_list:
            for child in arg_list.children:
                if child.type in ("string_literal", "string"):
                    raw = node_text(child).strip("'\"")
                    if raw.lower() in _WEAK_HASHES:
                        results.append({
                            "rule_id": "SEC-WEAK-CRYPTO",
                            "api": f"MessageDigest.getInstance(\"{raw}\")",
                            "algo": raw.upper(),
                            "line": node.start_point[0] + 1,
                            "file": rel_path,
                            "detail": (
                                f"MessageDigest.getInstance(\"{raw}\") uses a weak "
                                "cryptographic algorithm. Use SHA-256 or SHA-3."
                            ),
                        })

    return results


# ---------------------------------------------------------------------------
# JavaScript / TypeScript
# ---------------------------------------------------------------------------

def analyze_js_weak_crypto(tree, rel_path: str) -> list[dict]:
    """Detect crypto.createHash('md5') in JS/TS."""
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "call_expression":
            continue

        func = node.children[0] if node.children else None
        if func is None:
            continue
        func_text = node_text(func)

        if "createHash" not in func_text:
            continue

        # Check the first argument
        arg_list = next((c for c in node.children if c.type == "arguments"), None)
        if arg_list:
            for child in arg_list.children:
                if child.type == "string":
                    raw = node_text(child).strip("'\"")
                    if raw.lower() in _WEAK_HASHES:
                        results.append({
                            "rule_id": "SEC-WEAK-CRYPTO",
                            "api": f"createHash('{raw}')",
                            "algo": raw.upper(),
                            "line": node.start_point[0] + 1,
                            "file": rel_path,
                            "detail": (
                                f"crypto.createHash('{raw}') uses a weak hash. "
                                "Use 'sha256' or 'sha3-256' instead."
                            ),
                        })

    return results


# ---------------------------------------------------------------------------
# C++
# ---------------------------------------------------------------------------

_CPP_WEAK_CRYPTO_FNAMES = frozenset({
    "EVP_md5", "MD5_Init", "MD5_Update", "MD5_Final",
    "MD5", "SHA1_Init", "SHA1_Update", "SHA1_Final",
    "EVP_sha1",
})


def analyze_cpp_weak_crypto(tree, rel_path: str) -> list[dict]:
    """Detect OpenSSL MD5/SHA1 function calls in C++."""
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "call_expression":
            continue
        func = node.children[0] if node.children else None
        if func is None:
            continue
        fname = node_text(func)
        if fname in _CPP_WEAK_CRYPTO_FNAMES:
            algo = "MD5" if "md5" in fname.lower() or "MD5" in fname else "SHA-1"
            results.append({
                "rule_id": "SEC-WEAK-CRYPTO",
                "api": fname + "()",
                "algo": algo,
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    f"OpenSSL function `{fname}()` uses the weak {algo} algorithm. "
                    "Use EVP_sha256() or SHA-3 variants instead."
                ),
            })

    return results
