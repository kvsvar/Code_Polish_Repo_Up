"""
analysis/repair/repair_engine.py — Phase 5 Repair Engine.

Orchestrates candidate patch generation for a given finding.

Usage
-----
    from analysis.repair.repair_engine import get_candidate_patch
    response = get_candidate_patch(finding, project_root)

The engine NEVER modifies files. It only produces candidate Patch objects.

Architecture
------------
1. Look up RepairSpec in repair_registry.
2. If Tier 1 and autofix_available: load the handler module and call handler_fn.
3. Run patch validation (patch_model.validate_patch) on the candidate.
4. Return the RepairResponse with patch (or None) and verification_status.
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import Optional

from analysis.repair.patch_model import (
    Patch, PatchValidationError, validate_patch,
    TIER_1, TIER_2, TIER_3,
)
from analysis.repair.repair_registry import get_repair, RepairSpec

log = logging.getLogger(__name__)


class RepairResponse:
    """The result of a repair request for a single finding."""

    def __init__(
        self,
        finding: dict,
        repair_available: bool,
        tier: Optional[str],
        patch: Optional[Patch],
        validation_error: Optional[str],
        explanation: Optional[str],
    ):
        self.finding = finding
        self.repair_available = repair_available
        self.tier = tier
        self.patch = patch
        self.validation_error = validation_error
        self.explanation = explanation
        self.verification_status = "not_verified"

    def to_dict(self) -> dict:
        d: dict = {
            "finding": self.finding,
            "repair_available": self.repair_available,
            "tier": self.tier,
            "verification_status": self.verification_status,
        }
        if self.patch:
            d["patch"] = self.patch.to_dict()
        if self.validation_error:
            d["validation_error"] = self.validation_error
        if self.explanation:
            d["explanation"] = self.explanation
        return d


def get_candidate_patch(
    finding: dict,
    project_root: str,
) -> RepairResponse:
    """Generate a candidate patch for a finding (if a repair exists).

    Parameters
    ----------
    finding      : A finding dict as returned by to_dict() on a Finding object.
    project_root : Absolute path to the extracted project directory.
                   Used for path-escape validation.

    Returns
    -------
    RepairResponse — always returned; patch field is None if no fix available.
    """
    rule_id = finding.get("rule_id", "")
    language = finding.get("language") or _infer_language(finding.get("file", ""))

    spec = get_repair(rule_id, language)

    if spec is None:
        return RepairResponse(
            finding=finding,
            repair_available=False,
            tier=None,
            patch=None,
            validation_error=None,
            explanation=None,
        )

    # Tier 3 — explanation only
    if spec.tier == TIER_3:
        return RepairResponse(
            finding=finding,
            repair_available=False,
            tier=TIER_3,
            patch=None,
            validation_error=None,
            explanation=spec.description,
        )

    # Tier 2 — suggested (no auto-patch)
    if spec.tier == TIER_2 or not spec.autofix_available:
        return RepairResponse(
            finding=finding,
            repair_available=True,
            tier=TIER_2,
            patch=None,
            validation_error=None,
            explanation=spec.description,
        )

    # Tier 1 — attempt to generate a patch
    source_lines = _load_source_lines(finding.get("file", ""), project_root)
    if source_lines is None:
        return RepairResponse(
            finding=finding,
            repair_available=True,
            tier=TIER_1,
            patch=None,
            validation_error="Source file could not be read.",
            explanation=spec.description,
        )

    patch = _call_handler(spec, source_lines, finding)
    if patch is None:
        return RepairResponse(
            finding=finding,
            repair_available=True,
            tier=TIER_1,
            patch=None,
            validation_error="Repair handler could not generate a patch (pattern not found on the specified line).",
            explanation=spec.description,
        )

    # Validate the candidate patch
    try:
        validate_patch(patch, project_root, source_lines)
    except PatchValidationError as exc:
        log.warning("Patch validation failed for %s: %s", rule_id, exc)
        return RepairResponse(
            finding=finding,
            repair_available=True,
            tier=TIER_1,
            patch=None,
            validation_error=str(exc),
            explanation=spec.description,
        )

    return RepairResponse(
        finding=finding,
        repair_available=True,
        tier=TIER_1,
        patch=patch,
        validation_error=None,
        explanation=spec.description,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_source_lines(rel_file: str, project_root: str) -> Optional[list[str]]:
    """Safely read the source file. Returns None on any error."""
    if not rel_file:
        return None
    abs_path = os.path.normpath(os.path.join(project_root, rel_file))
    safe_root = os.path.normpath(project_root) + os.sep
    if not abs_path.startswith(safe_root):
        log.warning("Path escape attempt: %s", rel_file)
        return None
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.readlines()
    except Exception as exc:
        log.debug("Could not read %s: %s", abs_path, exc)
        return None


def _call_handler(spec: RepairSpec, source_lines: list[str], finding: dict) -> Optional[Patch]:
    """Dynamically load and call the repair handler."""
    if not spec.handler_module or not spec.handler_fn:
        return None
    try:
        mod = importlib.import_module(spec.handler_module)
        fn = getattr(mod, spec.handler_fn)
        return fn(source_lines, finding)
    except Exception as exc:
        log.exception("Repair handler %s.%s failed: %s", spec.handler_module, spec.handler_fn, exc)
        return None


def _infer_language(filepath: str) -> str:
    """Infer language from file extension when not set in finding."""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".hpp": "C++",
        ".h": "C++",
    }
    ext = os.path.splitext(filepath)[-1].lower()
    return ext_map.get(ext, "")
