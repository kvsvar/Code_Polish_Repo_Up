"""
analysis/rules/smells/formatting.py
CODE-FORMATTING — Source-level formatting anomalies detectable without a formatter.

Scope & limitations
-------------------
We deliberately avoid claiming to reproduce Pylint's W0311/W0312 semantics.
We implement only what can be reliably detected from raw source:

Python
------
  (a) Mixed indentation: file uses both tabs AND spaces for indentation.
      (Python explicitly forbids this in Python 3 — TabError.)
  (b) Trailing whitespace on non-blank lines (cosmetic but common in linters).

JavaScript / TypeScript / Java / C++
--------------------------------------
  Reliable indentation detection WITHOUT a full formatter requires a reference
  style (2-space, 4-space, tabs).  Without knowing the project's configured
  style, any check would have high FP rate.

  We implement one conservative check:
  (c) Mixed brace style: if a file uses BOTH
        } else {   (K&R / same-line)
      AND
        }
        else {     (Allman / next-line)
      it is a strong signal of mixed style.  We report it as one finding per file.

These checks operate on raw source text (not AST) — they're line-level.

Supported:
  Python  — mixed-indent detection  ✓
  JS/TS/Java/C++ — brace-style mixing  (conservative)
"""

from __future__ import annotations
import re

_SUPPORTED_INDENT_EXTS = {".py"}
_SUPPORTED_BRACE_EXTS = {".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".cc", ".cxx", ".h", ".hpp"}

_RE_TRAILING_WS = re.compile(r"[ \t]+$")
_RE_KNR = re.compile(r"\}\s*else\s*\{")           # K&R style
_RE_ALLMAN = re.compile(r"^\s*\}\s*$")             # lone closing brace line
_RE_ALLMAN_ELSE = re.compile(r"^\s*else\s*\{")     # Allman else on its own line


def check_python_formatting(lines: list[str], rel_path: str) -> list[dict]:
    """Detect mixed-indentation in a Python file."""
    has_tabs = False
    has_spaces = False
    first_tab_line = 0
    first_space_line = 0

    for i, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            continue
        leading = raw[:indent]
        if "\t" in leading:
            if not has_tabs:
                has_tabs = True
                first_tab_line = i
        if " " in leading:
            if not has_spaces:
                has_spaces = True
                first_space_line = i

    results = []
    if has_tabs and has_spaces:
        results.append({
            "rule_id": "CODE-FORMATTING",
            "issue": "mixed_indent",
            "detail": (
                f"File mixes tabs (first at line {first_tab_line}) and "
                f"spaces (first at line {first_space_line}) for indentation. "
                "Python 3 raises TabError for this."
            ),
            "line": min(first_tab_line, first_space_line),
            "file": rel_path,
        })

    # Trailing whitespace — report as a single summary if any found
    trailing_lines = []
    for i, raw in enumerate(lines, start=1):
        stripped = raw.rstrip("\r\n")
        if stripped and _RE_TRAILING_WS.search(stripped):
            trailing_lines.append(i)

    if len(trailing_lines) > 3:  # threshold to avoid noise on small files
        results.append({
            "rule_id": "CODE-FORMATTING",
            "issue": "trailing_whitespace",
            "detail": (
                f"File has trailing whitespace on {len(trailing_lines)} lines "
                f"(first at line {trailing_lines[0]})."
            ),
            "line": trailing_lines[0],
            "file": rel_path,
        })

    return results


def check_brace_style(lines: list[str], rel_path: str) -> list[dict]:
    """Detect mixed brace style in JS/TS/Java/C++ files."""
    knr_lines = []
    allman_else_lines = []

    for i, raw in enumerate(lines, start=1):
        stripped = raw.rstrip("\r\n")
        if _RE_KNR.search(stripped):
            knr_lines.append(i)
        if _RE_ALLMAN_ELSE.match(stripped):
            allman_else_lines.append(i)

    if knr_lines and allman_else_lines:
        return [{
            "rule_id": "CODE-FORMATTING",
            "issue": "mixed_brace_style",
            "detail": (
                f"File mixes K&R brace style (e.g. '}} else {{' at lines {knr_lines[:3]}) "
                f"and Allman/next-line style (e.g. 'else {{' at lines {allman_else_lines[:3]})."
            ),
            "line": min(knr_lines[0], allman_else_lines[0]),
            "file": rel_path,
        }]

    return []


def check_formatting(lines: list[str], rel_path: str) -> list[dict]:
    """Dispatch to the correct formatting check based on file extension."""
    import os
    ext = os.path.splitext(rel_path)[1].lower()

    if ext in _SUPPORTED_INDENT_EXTS:
        return check_python_formatting(lines, rel_path)
    elif ext in _SUPPORTED_BRACE_EXTS:
        return check_brace_style(lines, rel_path)
    return []
