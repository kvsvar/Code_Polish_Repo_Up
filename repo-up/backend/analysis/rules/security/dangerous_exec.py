"""
analysis/rules/security/dangerous_exec.py
SEC-DANGEROUS-EXEC — Dangerous Code Execution APIs

Expands and supersedes the existing SEC-AST-EVAL-EXEC rule.

CWE-78: OS Command Injection
CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code

Supported APIs per language
---------------------------
Python:
  eval(), exec()          — dynamic code execution (CWE-95)
  os.system()             — shell command execution (CWE-78)
  subprocess with shell=True  — shell injection vector (CWE-78)
  os.popen()              — shell command (CWE-78)
  commands.getoutput()    — deprecated but still seen (CWE-78)

JavaScript/TypeScript:
  eval()                  — dynamic code (CWE-95)
  new Function(...)       — dynamic code (CWE-95)
  child_process.exec()    — shell (CWE-78)
  child_process.execSync()
  child_process.spawn() with shell:true flag (CWE-78) — limited detection
  execFile() is NOT flagged (no shell expansion)

Java:
  Runtime.exec()          — shell (CWE-78)
  ProcessBuilder (flagged when .start() is chained) (CWE-78)

C++:
  system()                — shell (CWE-78)
  popen()                 — shell (CWE-78)
  execvp / execve / execl — lower severity, only flagged if in list

Limitations
-----------
* We detect the API, NOT whether user input is actually passed to it.
  A constant string passed to eval() is still flagged (conservative).
* subprocess.run() and subprocess.Popen() are ONLY flagged if shell=True
  is detectable in the keyword arguments.
* We do NOT flag os.path operations, file reading, or other safe uses.
"""

from __future__ import annotations
from analysis.rules.smells.ast_helpers import walk_depth_first, node_text, find_all

# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

_PY_DIRECT_EXEC = frozenset({"eval", "exec"})
_PY_SHELL_FUNCS = frozenset({"os.system", "os.popen", "commands.getoutput",
                              "commands.getstatusoutput"})
_PY_SUBPROCESS_FUNCS = frozenset({
    "subprocess.run", "subprocess.Popen", "subprocess.call",
    "subprocess.check_call", "subprocess.check_output",
    "run", "Popen", "call", "check_call", "check_output",
})


def _has_shell_true(call_node) -> bool:
    """Return True if call has keyword arg shell=True."""
    for kw in find_all(call_node, "keyword_argument"):
        children = kw.children
        if len(children) >= 3:
            k = node_text(children[0])
            v = node_text(children[-1])
            if k == "shell" and v in ("True", "1"):
                return True
    return False


def analyze_python_dangerous_exec(tree, rel_path: str) -> list[dict]:
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "call":
            continue
        func = node.children[0] if node.children else None
        if func is None:
            continue
        func_text = node_text(func)

        # eval / exec
        if func_text in _PY_DIRECT_EXEC:
            results.append({
                "rule_id": "SEC-DANGEROUS-EXEC",
                "api": func_text + "()",
                "cwe": "CWE-95",
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    f"`{func_text}()` executes arbitrary Python code at runtime. "
                    "If the input is attacker-controlled, this leads to code injection (CWE-95). "
                    "Replace with a safe parser or AST evaluation."
                ),
            })
            continue

        # os.system / os.popen
        if func_text in _PY_SHELL_FUNCS:
            results.append({
                "rule_id": "SEC-DANGEROUS-EXEC",
                "api": func_text + "()",
                "cwe": "CWE-78",
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    f"`{func_text}()` passes a command to the OS shell. "
                    "Passing unvalidated input leads to OS command injection (CWE-78). "
                    "Use subprocess.run() with a list argument and shell=False."
                ),
            })
            continue

        # subprocess.* with shell=True
        if func_text in _PY_SUBPROCESS_FUNCS and _has_shell_true(node):
            results.append({
                "rule_id": "SEC-DANGEROUS-EXEC",
                "api": func_text + "(shell=True)",
                "cwe": "CWE-78",
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    f"`{func_text}(shell=True)` enables shell interpretation of the command. "
                    "Pass a list of arguments and use shell=False to prevent injection (CWE-78)."
                ),
            })

    return results


# ---------------------------------------------------------------------------
# JavaScript / TypeScript
# ---------------------------------------------------------------------------

_JS_DIRECT_EXEC = frozenset({"eval"})
_JS_CHILD_PROCESS = frozenset({
    "exec", "execSync", "child_process.exec", "child_process.execSync",
})


def analyze_js_dangerous_exec(tree, rel_path: str) -> list[dict]:
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "call_expression":
            continue
        func = node.children[0] if node.children else None
        if func is None:
            continue
        func_text = node_text(func)

        # eval()
        if func_text == "eval":
            results.append({
                "rule_id": "SEC-DANGEROUS-EXEC",
                "api": "eval()",
                "cwe": "CWE-95",
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    "`eval()` executes a string as JavaScript code. "
                    "Attacker-controlled input leads to code injection (CWE-95). "
                    "Use JSON.parse() for data, or restructure to avoid dynamic evaluation."
                ),
            })
            continue

        # new Function(...)
        if func_text == "Function" or func_text.endswith(".Function"):
            # Only flag `new Function(...)` not `Function.prototype.bind()`
            parent = node.parent
            if parent and parent.type == "new_expression":
                results.append({
                    "rule_id": "SEC-DANGEROUS-EXEC",
                    "api": "new Function(...)",
                    "cwe": "CWE-95",
                    "line": node.start_point[0] + 1,
                    "file": rel_path,
                    "detail": (
                        "`new Function(...)` creates a function from a string, "
                        "equivalent to eval(). Attacker-controlled input leads to "
                        "code injection (CWE-95)."
                    ),
                })
                continue

        # child_process.exec / execSync
        if func_text in _JS_CHILD_PROCESS or (
            "." in func_text and func_text.rsplit(".", 1)[1] in ("exec", "execSync")
        ):
            results.append({
                "rule_id": "SEC-DANGEROUS-EXEC",
                "api": func_text + "()",
                "cwe": "CWE-78",
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": (
                    f"`{func_text}()` executes a shell command. "
                    "Passing user input leads to OS command injection (CWE-78). "
                    "Use execFile() with argument arrays, or validate all inputs strictly."
                ),
            })

    return results


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

def analyze_java_dangerous_exec(tree, rel_path: str) -> list[dict]:
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "method_invocation":
            continue

        children_texts = [node_text(c) for c in node.children]

        # Runtime.exec() / runtime.exec()
        if "exec" in children_texts:
            full = node_text(node)
            if "Runtime" in full or "runtime" in full:
                results.append({
                    "rule_id": "SEC-DANGEROUS-EXEC",
                    "api": "Runtime.exec()",
                    "cwe": "CWE-78",
                    "line": node.start_point[0] + 1,
                    "file": rel_path,
                    "detail": (
                        "Runtime.exec() executes an OS command. "
                        "Attacker-controlled input leads to OS command injection (CWE-78). "
                        "Use ProcessBuilder with a string[] argument and validate all inputs."
                    ),
                })
            continue

        # ProcessBuilder.start() — flag the start() call site
        if "start" in children_texts:
            full = node_text(node)
            if "ProcessBuilder" in full or "processBuilder" in full:
                results.append({
                    "rule_id": "SEC-DANGEROUS-EXEC",
                    "api": "ProcessBuilder.start()",
                    "cwe": "CWE-78",
                    "line": node.start_point[0] + 1,
                    "file": rel_path,
                    "detail": (
                        "ProcessBuilder.start() executes a system command. "
                        "Validate and sanitize all command arguments (CWE-78)."
                    ),
                })

    return results


# ---------------------------------------------------------------------------
# C++
# ---------------------------------------------------------------------------

_CPP_SHELL_FNAMES = frozenset({
    "system", "popen", "execl", "execle", "execlp",
    "execv", "execve", "execvp", "execvpe",
})


def analyze_cpp_dangerous_exec(tree, rel_path: str) -> list[dict]:
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type != "call_expression":
            continue
        func = node.children[0] if node.children else None
        if func is None:
            continue
        fname = node_text(func)

        if fname in _CPP_SHELL_FNAMES:
            cwe = "CWE-78"
            detail = (
                f"`{fname}()` executes a shell command or a new process. "
                "Passing attacker-controlled data leads to OS command injection (CWE-78). "
                "Validate all inputs; prefer safer alternatives where available."
            )
            results.append({
                "rule_id": "SEC-DANGEROUS-EXEC",
                "api": fname + "()",
                "cwe": cwe,
                "line": node.start_point[0] + 1,
                "file": rel_path,
                "detail": detail,
            })

    return results
