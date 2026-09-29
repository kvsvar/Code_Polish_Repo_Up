"""
analysis/repair/repairs/python_repairs.py — Tier 1 Python repair functions.

Each function accepts (source_lines, finding) and returns a Patch or None.

Safety constraints
------------------
- Only modify the exact token identified in the finding.
- If the expected old_text is not found at the specified location, return None.
- Never produce a patch whose new_text is semantically ambiguous.
"""

from __future__ import annotations

import re
from typing import Optional

from analysis.repair.patch_model import Patch, TIER_1


def fix_yaml_load(source_lines: list[str], finding: dict) -> Optional[Patch]:
    """Tier 1: Replace yaml.load(...) with yaml.safe_load(...) on the finding's line.

    Only replaces if:
    - The line contains 'yaml.load(' (not 'yaml.safe_load')
    - No Loader= keyword argument is already present that would change semantics

    Returns None if the condition cannot be verified.
    """
    line_no = finding.get("line")
    file_path = finding.get("file", "")
    if not line_no or not file_path:
        return None
    if line_no < 1 or line_no > len(source_lines):
        return None

    raw = source_lines[line_no - 1]

    # Only match bare yaml.load( — not yaml.safe_load(
    pattern = re.compile(r'\byaml\.load\s*\(')
    m = pattern.search(raw)
    if not m:
        return None

    old_token = m.group(0)          # e.g. "yaml.load("
    new_token = "yaml.safe_load("

    # Build old_text / new_text as whole-line replacement for clean diff
    new_line = raw[:m.start()] + new_token + raw[m.end():]
    old_text = raw
    new_text = new_line

    return Patch(
        rule_id="SEC-CWE-502",
        language="Python",
        tier=TIER_1,
        file=file_path,
        start_line=line_no,
        start_col=0,
        end_line=line_no,
        end_col=len(raw),
        old_text=old_text,
        new_text=new_text,
        description=(
            "Replace yaml.load() with yaml.safe_load(). "
            "yaml.safe_load() disables arbitrary Python object construction, "
            "eliminating the CWE-502 deserialization risk for standard YAML content."
        ),
    )


def fix_weak_hash_python(source_lines: list[str], finding: dict) -> Optional[Patch]:
    """Tier 1: Replace hashlib.md5() or hashlib.sha1() with hashlib.sha256().

    Matches: hashlib.md5(  or  hashlib.sha1(
    Does NOT match if already sha256/sha512.

    Returns None if pattern not found on the specified line.
    """
    line_no = finding.get("line")
    file_path = finding.get("file", "")
    if not line_no or not file_path:
        return None
    if line_no < 1 or line_no > len(source_lines):
        return None

    raw = source_lines[line_no - 1]

    # Match hashlib.md5( or hashlib.sha1( — case-insensitive for algorithm name
    pattern = re.compile(r'\bhashlib\.(md5|sha1)\s*\(', re.IGNORECASE)
    m = pattern.search(raw)
    if not m:
        return None

    old_token = m.group(0)
    new_token = re.sub(r'(md5|sha1)', 'sha256', old_token, flags=re.IGNORECASE)

    new_line = raw[:m.start()] + new_token + raw[m.end():]

    return Patch(
        rule_id="SEC-WEAK-CRYPTO",
        language="Python",
        tier=TIER_1,
        file=file_path,
        start_line=line_no,
        start_col=0,
        end_line=line_no,
        end_col=len(raw),
        old_text=raw,
        new_text=new_line,
        description=(
            f"Replace {m.group(0).strip()} with hashlib.sha256(). "
            "SHA-256 is cryptographically secure for general-purpose hashing. "
            "Note: for password storage, prefer hashlib.scrypt or bcrypt instead."
        ),
    )
