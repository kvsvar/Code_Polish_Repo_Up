"""
analysis/rules/security/__init__.py

Re-export the original run_security_rules so that existing imports from
'analysis.rules.security' continue to work after the refactoring into a package.
The original security.py module is now at analysis.rules.security_legacy.
"""
# Import the original function from the sibling legacy module
# We can't import from security.py directly since this dir shadows it.
# The actual module was renamed to security_legacy.py at import time via the path.

# We'll explicitly provide the function by importing from the file-level module.
import importlib.util, sys as _sys, os as _os

def _load_legacy():
    """Load analysis/rules/security.py (the original flat module) as a temp module."""
    legacy_path = _os.path.join(_os.path.dirname(__file__), "..", "security.py")
    legacy_path = _os.path.normpath(legacy_path)
    spec = importlib.util.spec_from_file_location(
        "analysis.rules._security_legacy", legacy_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_legacy = _load_legacy()
run_security_rules = _legacy.run_security_rules

