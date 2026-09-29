"""
analysis/rules/smells/public_methods.py
CODE-TOO-FEW-PUBLIC-METHODS — Class has fewer public methods than the minimum.

Approach
--------
Reuse the class-metric extraction from class_metrics.py (public_methods count).
This rule focuses on the smell of a class that is too small / thin.

Default threshold: MIN_PUBLIC_METHODS = 2
  (matches Pylint's default; a class with 0 or 1 public methods often should
   be a plain function or a constant, not a class)

Exclusions
----------
* Abstract base classes / interface declarations are skipped if detectable.
* Classes whose name ends in 'Mixin', 'Base', 'Abstract' are skipped.
* Classes with 0 public methods but non-zero fields (data classes) are also
  skipped (they're not smell — they're pure data containers).
* Test classes (name starts with 'Test' or ends with 'Test'/'Tests') are skipped.
* Module-level synthetic "Module Level" entries from class_metrics are skipped.

Supported: Python, JavaScript, TypeScript, Java, C++
(relies on class_metrics.compute_class_metrics which handles all five)
"""

from __future__ import annotations

MIN_PUBLIC_METHODS = 2  # configurable

_SKIP_SUFFIXES = ("mixin", "base", "abstract", "interface")
_SKIP_PREFIXES = ("abstract",)
_TEST_PREFIXES = ("test",)
_TEST_SUFFIXES = ("test", "tests", "spec", "specs")


def _should_skip(class_name: str) -> bool:
    name_lower = class_name.lower()
    if name_lower == "module level":
        return True
    if any(name_lower.endswith(s) for s in _SKIP_SUFFIXES):
        return True
    if any(name_lower.startswith(s) for s in _SKIP_PREFIXES):
        return True
    if any(name_lower.startswith(s) for s in _TEST_PREFIXES):
        return True
    if any(name_lower.endswith(s) for s in _TEST_SUFFIXES):
        return True
    return False


def check_too_few_public_methods(
    class_metrics: list[dict],
    min_methods: int = MIN_PUBLIC_METHODS,
) -> list[dict]:
    """Check each class in *class_metrics* for too few public methods.

    Parameters
    ----------
    class_metrics : list of dicts from compute_class_metrics()
    min_methods   : minimum required public method count

    Returns
    -------
    List of raw finding dicts (to be wrapped by smell_engine.py).
    """
    results = []
    for cls in class_metrics:
        name = cls.get("name", "")
        if _should_skip(name):
            continue
        pub = cls.get("public_methods", 0)
        # Skip data-only classes (0 methods but has fields)
        if pub == 0 and cls.get("public_fields", 0) > 0:
            continue
        if pub < min_methods:
            results.append({
                "rule_id": "CODE-TOO-FEW-PUBLIC-METHODS",
                "class_name": name,
                "public_methods": pub,
                "min_methods": min_methods,
                "line": cls.get("line", 1),
                "file": cls.get("filepath", ""),
            })
    return results
