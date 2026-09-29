"""
analysis/repair/repairs/java_repairs.py — Tier 1 Java repair functions.

Each function accepts (source_lines, finding) and returns a Patch or None.
"""

from __future__ import annotations

import re
from typing import Optional

from analysis.repair.patch_model import Patch, TIER_1


def fix_weak_hash_java(source_lines: list[str], finding: dict) -> Optional[Patch]:
    """Tier 1: Replace MessageDigest.getInstance("MD5") or "SHA-1" with "SHA-256".

    Matches: MessageDigest.getInstance("MD5"), ("MD5"), ("SHA-1"), ("SHA1")
    Handles both single and double quotes (though Java typically uses double).
    Returns None if the pattern is not found on the finding's line.
    """
    line_no = finding.get("line")
    file_path = finding.get("file", "")
    if not line_no or not file_path:
        return None
    if line_no < 1 or line_no > len(source_lines):
        return None

    raw = source_lines[line_no - 1]

    # Match: getInstance("MD5") or getInstance("SHA-1") or getInstance("SHA1")
    pattern = re.compile(
        r"""getInstance\s*\(\s*"(MD5|SHA-?1|md5|sha-?1)"\s*\)""",
        re.IGNORECASE,
    )
    m = pattern.search(raw)
    if not m:
        return None

    old_token = m.group(0)
    new_token = 'getInstance("SHA-256")'

    new_line = raw[:m.start()] + new_token + raw[m.end():]

    return Patch(
        rule_id="SEC-WEAK-CRYPTO",
        language="Java",
        tier=TIER_1,
        file=file_path,
        start_line=line_no,
        start_col=0,
        end_line=line_no,
        end_col=len(raw),
        old_text=raw,
        new_text=new_line,
        description=(
            f"Replace MessageDigest.getInstance(\"{m.group(1)}\") "
            "with getInstance(\"SHA-256\"). "
            "SHA-256 is FIPS-140-2 compliant and cryptographically secure."
        ),
    )
