"""
analysis/rules/security/exception_handling.py
SEC-CWE-703 — Improper Check or Handling of Exceptional Conditions

CWE-703: Improper Check or Handling of Exceptional Conditions

This replaces the coarse "I/O import exists but no try/catch" check with
a more meaningful per-operation analysis.

Approach
--------
For each function/method body:
  1. Identify "risky operations" — calls to I/O, network, DB, filesystem APIs
  2. Check if those calls are wrapped in a try/except (or try/catch)
  3. Report uncovered risky calls, NOT just "file has I/O + no try"

A call is "covered" if it is a syntactic descendant of a try block.

Supported: Python, JavaScript/TypeScript, Java
Not supported: C++ (exception handling requires type resolution to be reliable)

Limitation
----------
* We check SYNTACTIC enclosure in a try block, NOT semantic coverage.
  A try/except that only catches MemoryError would still count as covered here.
* Broad except clauses (bare except:, except Exception:) are NOT additionally
  penalized in this rule — that's a separate quality concern.
"""

from __future__ import annotations
from analysis.rules.smells.ast_helpers import walk_depth_first, node_text, find_all

# ---------------------------------------------------------------------------
# Risky operation patterns per language
# ---------------------------------------------------------------------------

_PY_RISKY_MODULES = frozenset({
    "requests", "urllib", "urllib2", "http", "socket", "ssl",
    "ftplib", "smtplib", "paramiko",
    "os", "shutil", "pathlib", "io",
    "sqlite3", "psycopg2", "pymongo", "redis",
    "subprocess",
})

_PY_RISKY_METHODS = frozenset({
    # filesystem
    "open", "read", "write", "unlink", "rmdir", "makedirs",
    # network
    "get", "post", "put", "delete", "request", "urlopen", "connect",
    # subprocess
    "run", "Popen", "call", "check_output",
    # DB
    "execute", "executemany", "cursor", "commit",
})

_JS_RISKY_METHODS = frozenset({
    "readFile", "readFileSync", "writeFile", "writeFileSync",
    "fetch", "axios", "request", "get", "post",
    "connect", "query", "execute",
    "exec", "execSync", "spawn",
    "open", "read", "write",
})

_JAVA_RISKY_TYPES = frozenset({
    "FileInputStream", "FileOutputStream", "FileReader", "FileWriter",
    "BufferedReader", "Socket", "ServerSocket",
    "HttpURLConnection", "URL",
    "PreparedStatement", "Statement", "Connection",
    "Runtime",
})


# ---------------------------------------------------------------------------
# Helper: is node inside a try block?
# ---------------------------------------------------------------------------

def _is_inside_try(node, try_types=("try_statement",)) -> bool:
    """Walk up the parent chain looking for a try block."""
    current = node.parent
    while current is not None:
        if current.type in try_types:
            return True
        current = current.parent
    return False


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

def analyze_python_exc_handling(tree, rel_path: str) -> list[dict]:
    """Flag risky Python calls that are NOT inside a try/except."""
    results: list[dict] = []
    seen: set[tuple] = set()

    for node in walk_depth_first(tree.root_node):
        if node.type != "call":
            continue

        func = node.children[0] if node.children else None
        if func is None:
            continue
        func_text = node_text(func)

        # Check if it's a risky method call
        method = func_text.split(".")[-1]
        module = func_text.split(".")[0] if "." in func_text else ""

        is_risky = (
            method in _PY_RISKY_METHODS or
            module in _PY_RISKY_MODULES
        ) and func_text not in ("print", "len", "range", "str", "int")

        if not is_risky:
            continue

        if _is_inside_try(node, ("try_statement",)):
            continue

        line = node.start_point[0] + 1
        key = (rel_path, func_text, line)
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "rule_id": "SEC-CWE-703",
            "api": func_text,
            "line": line,
            "file": rel_path,
            "detail": (
                f"Call to `{func_text}()` is not enclosed in a try/except block. "
                "If this operation fails (network error, missing file, permission denied), "
                "the exception will propagate unhandled (CWE-703). "
                "Wrap in try/except and handle or log the exception appropriately."
            ),
        })

    return results


# ---------------------------------------------------------------------------
# JavaScript / TypeScript
# ---------------------------------------------------------------------------

def analyze_js_exc_handling(tree, rel_path: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple] = set()

    for node in walk_depth_first(tree.root_node):
        if node.type != "call_expression":
            continue

        func = node.children[0] if node.children else None
        if func is None:
            continue
        func_text = node_text(func)
        method = func_text.rsplit(".", 1)[-1] if "." in func_text else func_text

        if method not in _JS_RISKY_METHODS:
            continue

        if _is_inside_try(node, ("try_statement",)):
            continue

        line = node.start_point[0] + 1
        key = (rel_path, func_text, line)
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "rule_id": "SEC-CWE-703",
            "api": func_text,
            "line": line,
            "file": rel_path,
            "detail": (
                f"Call to `{func_text}()` is not enclosed in a try/catch block. "
                "I/O and network operations can fail; unhandled rejections or exceptions "
                "can crash the process or expose stack traces (CWE-703). "
                "Wrap in try/catch or handle promise rejections."
            ),
        })

    return results


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

def analyze_java_exc_handling(tree, rel_path: str) -> list[dict]:
    """Flag Java object creation of risky types outside try blocks."""
    results: list[dict] = []
    seen: set[tuple] = set()

    for node in walk_depth_first(tree.root_node):
        # object_creation_expression: new FileInputStream(...)
        if node.type == "object_creation_expression":
            for child in node.children:
                if child.type in ("type_identifier", "identifier"):
                    type_name = node_text(child)
                    if type_name in _JAVA_RISKY_TYPES:
                        if not _is_inside_try(node, ("try_statement",
                                                      "try_with_resources_statement")):
                            line = node.start_point[0] + 1
                            key = (rel_path, type_name, line)
                            if key not in seen:
                                seen.add(key)
                                results.append({
                                    "rule_id": "SEC-CWE-703",
                                    "api": f"new {type_name}()",
                                    "line": line,
                                    "file": rel_path,
                                    "detail": (
                                        f"Instantiation of `{type_name}` outside a try/catch block. "
                                        "Resource acquisition and I/O operations can throw "
                                        "checked exceptions that must be handled (CWE-703)."
                                    ),
                                })
                    break

    return results
