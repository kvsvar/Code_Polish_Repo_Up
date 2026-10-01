"""
analysis/finding.py — Unified Finding model for the Repo-Up analysis pipeline.

Design goals
------------
* All analysis rules produce Finding objects instead of raw dicts.
* to_dict() serialises to the exact shape the frontend already expects, so NO
  frontend changes are needed.
* The richer fields (id, rule, language, cwe, resolution, autofix_available)
  are available to later phases (repair, explanation, evaluation) without
  breaking the current API.

Compatibility note
------------------
The existing API result["issues"] is List[dict].  Rules now return
List[Finding]; analyze.py calls finding.to_dict() before adding to the
result.  The resulting wire format is identical to the current dict structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Finding:
    """A normalised analysis finding produced by any rule or metric check.

    Required fields
    ---------------
    rule_id   : stable identifier from RULE_REGISTRY (e.g. "SEC-EVAL-EXEC")
    category  : display category — "Structural" | "Security" | "Metrics"
    title     : short human-readable title (shown in the findings list)
    description : detailed explanation / evidence text
    severity  : "High" | "Medium" | "Low"

    Optional fields
    ---------------
    rule      : human-readable rule name (defaults to rule_id)
    language  : language the rule applies to, or None for language-agnostic rules
    file      : relative path to the source file containing the finding
    line      : 1-indexed line number within file
    column    : 1-indexed column number within file
    cwe       : CWE identifier string, e.g. "CWE-78"
    resolution: short actionable fix suggestion
    autofix_available : whether an automated fix exists (Phase 4+)
    verified  : whether a test-based verification was run (Phase 3+)
    """

    rule_id: str
    category: str
    title: str
    description: str
    severity: str  # "High" | "Medium" | "Low"

    rule: Optional[str] = None
    language: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    cwe: Optional[str] = None
    resolution: Optional[str] = None
    autofix_available: bool = False
    verified: bool = False
    source: str = "Native"

    def to_dict(self) -> dict:
        """Serialise to the wire shape currently expected by Results.tsx.

        The frontend interface is:
            { category, title, description, severity, file?, line? }

        All richer fields are included in the serialisation under their own
        keys so they are available in the JSON report download and for future
        frontend features, but the frontend currently ignores unknown keys --
        it will not break.
        """
        d: dict = {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            # Richer fields -- ignored by current frontend, used by future phases
            "rule_id": self.rule_id,
        }
        if self.rule is not None:
            d["rule"] = self.rule
        if self.language is not None:
            d["language"] = self.language
        if self.file is not None:
            d["file"] = self.file
        if self.line is not None:
            d["line"] = self.line
        if self.column is not None:
            d["column"] = self.column
        if self.cwe is not None:
            d["cwe"] = self.cwe
        if self.resolution is not None:
            d["resolution"] = self.resolution
        if self.autofix_available:
            d["autofix_available"] = True
        if self.verified:
            d["verified"] = True
        if self.source:
            d["source"] = self.source
        return d

    @staticmethod
    def from_dict(d: dict) -> "Finding":
        """Reconstruct a Finding from a serialised dict (e.g. for tests)."""
        return Finding(
            rule_id=d.get("rule_id", "UNKNOWN"),
            category=d.get("category", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            severity=d.get("severity", "Medium"),
            rule=d.get("rule"),
            language=d.get("language"),
            file=d.get("file"),
            line=d.get("line"),
            column=d.get("column"),
            cwe=d.get("cwe"),
            resolution=d.get("resolution"),
            autofix_available=d.get("autofix_available", False),
            verified=d.get("verified", False),
            source=d.get("source", "Native"),
        )
