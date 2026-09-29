"""
analysis/repair/repairs/js_repairs.py — Tier 1 JavaScript/TypeScript repair functions.

Each function accepts (source_lines, finding) and returns a Patch or None.

Note: JS and TS share the same repair because the crypto API is identical.
"""

from __future__ import annotations

import re
from typing import Optional

from analysis.repair.patch_model import Patch, TIER_1


def fix_weak_hash_js(source_lines: list[str], finding: dict) -> Optional[Patch]:
    """Tier 1: Replace crypto.createHash('md5') or crypto.createHash('sha1')
    with crypto.createHash('sha256').

    Works for both single-quoted and double-quoted string arguments.
    Returns None if the pattern is not found on the finding's line.
    """
    line_no = finding.get("line")
    file_path = finding.get("file", "")
    language = finding.get("language", "JavaScript")
    if not line_no or not file_path:
        return None
    if line_no < 1 or line_no > len(source_lines):
        return None

    raw = source_lines[line_no - 1]

    # Match: createHash('md5') or createHash("md5") or createHash('sha1') etc.
    pattern = re.compile(
        r"""createHash\s*\(\s*(['"])(md5|sha1|MD5|SHA1|SHA-1|sha-1)\1\s*\)""",
        re.IGNORECASE,
    )
    m = pattern.search(raw)
    if not m:
        return None

    quote = m.group(1)
    old_token = m.group(0)
    new_token = f"createHash({quote}sha256{quote})"

    new_line = raw[:m.start()] + new_token + raw[m.end():]

    return Patch(
        rule_id="SEC-WEAK-CRYPTO",
        language=language,
        tier=TIER_1,
        file=file_path,
        start_line=line_no,
        start_col=0,
        end_line=line_no,
        end_col=len(raw),
        old_text=raw,
        new_text=new_line,
        description=(
            f"Replace {old_token.strip()} with createHash('sha256'). "
            "SHA-256 is cryptographically secure for general-purpose hashing."
        ),
    )
