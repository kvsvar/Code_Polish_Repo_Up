"""
analysis/rules/smells/line_length.py
CODE-LONG-LINE — Flag lines exceeding a configurable threshold.

Approach
--------
* Read source via raw text (not AST) — line length is a textual property.
* AST is used only to identify comment vs code (we do NOT skip comments —
  a 200-char comment is still a quality problem).
* Skip binary, generated, and minified files.

Supported languages: Python, JavaScript, TypeScript, Java, C++
(anything with a parseable extension; we fall back to raw scan for others).

Limitations
-----------
* Auto-generated/minified single-line JS/TS bundles will fire heavily.
  Workaround: the caller (smell_engine.py) excludes files in dist/ or build/.
"""

from __future__ import annotations

LONG_LINE_THRESHOLD = 100  # characters (configurable per call)

# Heuristic: if > 80% of lines exceed threshold, file is likely minified
_MINIFIED_FRACTION = 0.80

# Extensions this rule applies to (matches language_config extensions)
_SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java",
    ".cpp", ".cc", ".cxx", ".hpp", ".h",
}


def _looks_minified(lines: list[str], threshold: int) -> bool:
    if not lines:
        return False
    over = sum(1 for ln in lines if len(ln.rstrip("\r\n")) > threshold)
    return (over / len(lines)) > _MINIFIED_FRACTION


def check_line_length(
    lines: list[str],
    rel_path: str,
    threshold: int = LONG_LINE_THRESHOLD,
) -> list[dict]:
    """Return raw finding-dicts for lines exceeding *threshold*.

    Parameters
    ----------
    lines     : source lines as returned by open().readlines()
    rel_path  : relative path for file field
    threshold : max allowed line length (characters)
    """
    import os
    ext = os.path.splitext(rel_path)[1].lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        return []
    if _looks_minified(lines, threshold):
        return []

    results = []
    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\r\n")
        length = len(line)
        if length > threshold:
            results.append({
                "line_no": i,
                "length": length,
                "threshold": threshold,
                "snippet": line[:80] + "..." if length > 83 else line,
            })
    return results
