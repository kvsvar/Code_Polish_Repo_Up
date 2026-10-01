"""
verification/test_runner.py - Discovery and execution of runtime tests.
"""
import os
import platform
from typing import Optional, Tuple
from .limits import MAX_RUNTIME_SECONDS

def discover_and_run_tests(workspace_path: str) -> Tuple[str, str, str]:
    """
    Detects known test conventions and runs them.
    Returns (status, stdout, stderr). Status can be 'PASS', 'FAIL', 'NOT_AVAILABLE', 'TIMEOUT'.
    """
    # Windows lacks native unprivileged container isolation (namespaces/cgroups).
    # To satisfy safety constraints (no arbitrary shell commands, restricted network/process),
    # we explicitly disable runtime tests on Windows unless a specialized container runtime is provided.
    if platform.system() == "Windows":
        return "NOT_AVAILABLE", "", "Runtime test sandboxing is natively unavailable on Windows."

    has_package_json = os.path.exists(os.path.join(workspace_path, "package.json"))
    has_pytest = os.path.exists(os.path.join(workspace_path, "pytest.ini")) or \
                 os.path.exists(os.path.join(workspace_path, "tests"))

    # For now, mark as not available to strictly adhere to "no fake sandbox" safety rule.
    return "NOT_AVAILABLE", "", "True OS isolation guarantees not present; runtime tests disabled."
