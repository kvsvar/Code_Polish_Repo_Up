"""
analysis/repair/repair_registry.py — Phase 5 Repair Registry.

Every repair strategy is registered here with:
  - rule_id        : The finding rule this repair addresses.
  - language       : Target language ("Python", "Java", "JavaScript", "TypeScript", "C++").
  - tier           : TIER_1 | TIER_2 | TIER_3 (see patch_model.py).
  - deterministic  : True = always produces the same patch given the same input.
  - autofix_available : True = a Patch object can be generated (Tier 1 only).
  - required_context  : What inputs the repair function needs.
  - handler        : Dotted import path to the repair function.

Tier classification (Step 2)
-----------------------------
TIER_1 — Deterministic automatic fix. Patch generated, never auto-applied.
TIER_2 — Suggested patch requiring review. Function exists but may be ambiguous.
TIER_3 — Explanation only. No patch code.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable

from analysis.repair.patch_model import TIER_1, TIER_2, TIER_3


@dataclass(frozen=True)
class RepairSpec:
    """Descriptor for a single repair strategy."""

    rule_id: str
    language: str
    tier: str
    deterministic: bool
    autofix_available: bool
    required_context: tuple[str, ...]
    description: str
    handler_module: str   # dotted module path
    handler_fn: str       # function name within module


# ---------------------------------------------------------------------------
# Registry store
# ---------------------------------------------------------------------------
_REGISTRY: dict[tuple[str, str], RepairSpec] = {}


def _reg(spec: RepairSpec) -> None:
    _REGISTRY[(spec.rule_id, spec.language)] = spec


def get_repair(rule_id: str, language: str) -> Optional[RepairSpec]:
    """Look up a repair spec by rule_id + language. Returns None if not found."""
    return _REGISTRY.get((rule_id, language))


def list_repairs() -> list[RepairSpec]:
    """Return all registered repair specs."""
    return list(_REGISTRY.values())


def has_autofix(rule_id: str, language: str) -> bool:
    spec = get_repair(rule_id, language)
    return bool(spec and spec.autofix_available)


# ===========================================================================
# Registrations — Tier 1 (Deterministic)
# ===========================================================================

# --- Python: yaml.load → yaml.safe_load (SEC-CWE-502) ---
_reg(RepairSpec(
    rule_id="SEC-CWE-502",
    language="Python",
    tier=TIER_1,
    deterministic=True,
    autofix_available=True,
    required_context=("file", "line", "source_lines"),
    description=(
        "Replace yaml.load(stream) with yaml.safe_load(stream). "
        "This is a direct, unambiguous API substitution with identical semantics "
        "for safe YAML content."
    ),
    handler_module="analysis.repair.repairs.python_repairs",
    handler_fn="fix_yaml_load",
))

# --- Python: hashlib.md5 / hashlib.sha1 → hashlib.sha256 (SEC-WEAK-CRYPTO) ---
_reg(RepairSpec(
    rule_id="SEC-WEAK-CRYPTO",
    language="Python",
    tier=TIER_1,
    deterministic=True,
    autofix_available=True,
    required_context=("file", "line", "source_lines"),
    description=(
        "Replace hashlib.md5() or hashlib.sha1() with hashlib.sha256(). "
        "Safe only when the hash is used for general-purpose integrity, "
        "not for a password-specific KDF (those need bcrypt/scrypt)."
    ),
    handler_module="analysis.repair.repairs.python_repairs",
    handler_fn="fix_weak_hash_python",
))

# --- JavaScript/TypeScript: crypto.createHash('md5'/'sha1') → 'sha256' (SEC-WEAK-CRYPTO) ---
_reg(RepairSpec(
    rule_id="SEC-WEAK-CRYPTO",
    language="JavaScript",
    tier=TIER_1,
    deterministic=True,
    autofix_available=True,
    required_context=("file", "line", "source_lines"),
    description=(
        "Replace crypto.createHash('md5') or crypto.createHash('sha1') "
        "with crypto.createHash('sha256'). Direct string substitution."
    ),
    handler_module="analysis.repair.repairs.js_repairs",
    handler_fn="fix_weak_hash_js",
))

_reg(RepairSpec(
    rule_id="SEC-WEAK-CRYPTO",
    language="TypeScript",
    tier=TIER_1,
    deterministic=True,
    autofix_available=True,
    required_context=("file", "line", "source_lines"),
    description=(
        "Replace crypto.createHash('md5') or crypto.createHash('sha1') "
        "with crypto.createHash('sha256'). Direct string substitution."
    ),
    handler_module="analysis.repair.repairs.js_repairs",
    handler_fn="fix_weak_hash_js",
))

# --- Java: MessageDigest.getInstance("MD5"/"SHA-1") → "SHA-256" (SEC-WEAK-CRYPTO) ---
_reg(RepairSpec(
    rule_id="SEC-WEAK-CRYPTO",
    language="Java",
    tier=TIER_1,
    deterministic=True,
    autofix_available=True,
    required_context=("file", "line", "source_lines"),
    description=(
        "Replace MessageDigest.getInstance(\"MD5\") or \"SHA-1\" "
        "with \"SHA-256\". Direct string substitution within the getInstance() call."
    ),
    handler_module="analysis.repair.repairs.java_repairs",
    handler_fn="fix_weak_hash_java",
))

# ===========================================================================
# Registrations — Tier 2 (Suggested, require review)
# ===========================================================================

# --- Python: pickle.loads / marshal.loads → explanation + json alternative (SEC-CWE-502) ---
_reg(RepairSpec(
    rule_id="SEC-CWE-502",
    language="Java",
    tier=TIER_2,
    deterministic=False,
    autofix_available=False,
    required_context=("file", "line"),
    description=(
        "Java ObjectInputStream.readObject() deserialization cannot be safely "
        "auto-replaced without knowing the target class structure. "
        "Suggested: add a serialization filter via ObjectInputFilter (Java 9+) "
        "or switch to a JSON/Protobuf serialization library."
    ),
    handler_module="",
    handler_fn="",
))

# --- Python: os.system / subprocess shell=True → Tier 2 (SEC-DANGEROUS-EXEC) ---
_reg(RepairSpec(
    rule_id="SEC-DANGEROUS-EXEC",
    language="Python",
    tier=TIER_2,
    deterministic=False,
    autofix_available=False,
    required_context=("file", "line"),
    description=(
        "Replacing os.system() or subprocess(shell=True) requires knowing the "
        "command arguments to safely split into a list. "
        "Suggested: use subprocess.run([...], shell=False). "
        "Manual review required to determine safe argument structure."
    ),
    handler_module="",
    handler_fn="",
))

# --- Python: eval() → Tier 2 (SEC-DANGEROUS-EXEC) ---
_reg(RepairSpec(
    rule_id="SEC-DANGEROUS-EXEC",
    language="JavaScript",
    tier=TIER_2,
    deterministic=False,
    autofix_available=False,
    required_context=("file", "line"),
    description=(
        "eval() / exec() replacement depends on the intended semantics. "
        "Suggested alternatives: JSON.parse() for data, Function() with "
        "strict restrictions, or refactoring to avoid dynamic evaluation. "
        "Manual review required."
    ),
    handler_module="",
    handler_fn="",
))

# ===========================================================================
# Registrations — Tier 3 (Explanation only)
# ===========================================================================

_reg(RepairSpec(
    rule_id="SEC-UNSAFE-ASSERT",
    language="Python",
    tier=TIER_3,
    deterministic=False,
    autofix_available=False,
    required_context=("file", "line"),
    description=(
        "Replace the assert statement with an explicit conditional and raise "
        "an appropriate exception such as PermissionError, ValueError, or "
        "HTTPException(status_code=403). The assert must be replaced — not "
        "merely removed — to preserve the security intent."
    ),
    handler_module="",
    handler_fn="",
))

_reg(RepairSpec(
    rule_id="SEC-CWE-703",
    language="Python",
    tier=TIER_3,
    deterministic=False,
    autofix_available=False,
    required_context=("file", "line"),
    description=(
        "Wrap the risky I/O or network call in a try/except block. "
        "The specific exceptions to catch depend on the operation: "
        "OSError for file I/O, requests.exceptions.RequestException for HTTP, "
        "etc. Manual addition required to preserve correct error handling logic."
    ),
    handler_module="",
    handler_fn="",
))
