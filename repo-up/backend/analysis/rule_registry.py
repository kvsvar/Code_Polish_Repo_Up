"""
analysis/rule_registry.py — Metadata registry of all rules implemented in Repo-Up.

PURPOSE
-------
This module is METADATA ONLY.  It does not execute rules.
It maps stable rule IDs to descriptive metadata that describes each rule so
that later phases (explanation, repair, verification) can look up context
without hardcoding it in analyze.py.

The registry enables the pipeline:
    Rule ID
      -> Detection  (existing rules, now tagged with rule_id)
      -> Explanation (future: LLM-assisted)
      -> Repair      (future: Phase 4 sandbox)
      -> Verification (future: Phase 3 tests)

RULE ID CONVENTIONS
-------------------
STRUCT-   Structural / project-layout rules
SEC-      Security rules (regex-based secret detection)
SEC-AST-  Security rules requiring AST analysis
METRIC-   Metric-threshold findings

CWE references
--------------
CWE-321  Use of Hard-coded Cryptographic Key
CWE-798  Use of Hard-coded Credentials
CWE-78   OS Command Injection (eval/exec)
CWE-502  Deserialization of Untrusted Data (exec)
CWE-703  Improper Check or Handling of Exceptional Conditions
CWE-1062 Parent Class with Virtual Destructor and Child Class without one
         (re-used here loosely for "deep inheritance")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class RuleSpec:
    """Immutable descriptor for a single analysis rule."""

    rule_id: str
    """Stable unique identifier, e.g. 'SEC-HARDCODED-SECRET'."""

    category: str
    """Display category: 'Structural' | 'Security' | 'Metrics'."""

    name: str
    """Human-readable rule name."""

    description: str
    """One-line explanation of what the rule checks."""

    severity: str
    """Default severity: 'High' | 'Medium' | 'Low'."""

    languages: tuple[str, ...]
    """Languages this rule applies to. Empty tuple = language-agnostic."""

    cwe: Optional[str] = None
    """Common Weakness Enumeration reference, e.g. 'CWE-798'."""

    resolution: Optional[str] = None
    """Short actionable fix text."""

    autofix_available: bool = False
    """True when Phase 4 can automatically apply a fix."""

    module_reference: str = ""
    """Dotted path to the implementing function (informational)."""


# ---------------------------------------------------------------------------
# Registry — one entry per rule that currently exists in the codebase
# ---------------------------------------------------------------------------
RULE_REGISTRY: dict[str, RuleSpec] = {}


def _reg(spec: RuleSpec) -> None:
    RULE_REGISTRY[spec.rule_id] = spec


# -- Structural rules (structural.py) ----------------------------------------

_reg(RuleSpec(
    rule_id="STRUCT-MISSING-README",
    category="Structural",
    name="Missing README",
    description="Project root contains no README.md documentation file.",
    severity="High",
    languages=(),
    resolution="Add a README.md at the project root describing setup, usage, and architecture.",
    module_reference="analysis.rules.structural.run_structural_rules",
))

_reg(RuleSpec(
    rule_id="STRUCT-MISSING-SRC",
    category="Structural",
    name="No src folder",
    description="Source files are placed in the project root rather than a src/ directory.",
    severity="Medium",
    languages=(),
    resolution="Organise source code under a src/ subdirectory.",
    module_reference="analysis.rules.structural.run_structural_rules",
))

_reg(RuleSpec(
    rule_id="STRUCT-MISSING-TESTS",
    category="Structural",
    name="No tests folder",
    description="Project lacks a dedicated tests/ or test/ directory.",
    severity="High",
    languages=(),
    resolution="Create a tests/ directory and add unit/integration tests.",
    module_reference="analysis.rules.structural.run_structural_rules",
))

_reg(RuleSpec(
    rule_id="STRUCT-MISSING-DEPS",
    category="Structural",
    name="Missing dependencies file",
    description="Project has neither a requirements.txt nor a package.json dependency manifest.",
    severity="High",
    languages=(),
    resolution="Add requirements.txt (Python) or package.json (JS/TS) listing all dependencies.",
    module_reference="analysis.rules.structural.run_structural_rules",
))

_reg(RuleSpec(
    rule_id="STRUCT-MISSING-ENV-EXAMPLE",
    category="Structural",
    name="Missing .env.example",
    description="Project lacks a .env.example template documenting required environment variables.",
    severity="Medium",
    languages=(),
    resolution="Add a .env.example file listing all required environment variables with placeholder values.",
    module_reference="analysis.rules.structural.run_structural_rules",
))

_reg(RuleSpec(
    rule_id="STRUCT-CIRCULAR-DEP",
    category="Structural",
    name="Circular Dependency",
    description="Two or more modules import each other, forming a dependency cycle (detected via Tarjan SCC).",
    severity="High",
    languages=(),
    resolution="Refactor shared logic into a third module that neither of the cyclic modules imports.",
    module_reference="analysis.metrics.graph_metrics.detect_circular_dependencies",
))

# -- Security rules (regex-based, security.py) --------------------------------

_reg(RuleSpec(
    rule_id="SEC-COMMITTED-ENV",
    category="Security",
    name="Committed Environment File",
    description="A .env file containing environment secrets is committed to source control.",
    severity="High",
    languages=(),
    cwe="CWE-798",
    resolution="Remove the .env file from version control, add it to .gitignore, and rotate any exposed credentials.",
    module_reference="analysis.rules.security.run_security_rules",
))

_reg(RuleSpec(
    rule_id="SEC-HARDCODED-SECRET",
    category="Security",
    name="Hardcoded Secret",
    description="A string matching a known API key or credential pattern was found in source code.",
    severity="High",
    languages=(),
    cwe="CWE-798",
    resolution="Move credentials to environment variables or a secrets manager. Never commit real credentials.",
    module_reference="analysis.rules.security.run_security_rules",
))

# -- AST security rules (ast_security.py) -------------------------------------

_reg(RuleSpec(
    rule_id="SEC-AST-EVAL-EXEC",
    category="Security",
    name="Dangerous Function Usage",
    description="eval(), exec(), or system() was found in the AST. These functions can execute arbitrary code.",
    severity="High",
    languages=("Python", "JavaScript", "TypeScript", "C++"),
    cwe="CWE-78",
    resolution="Replace eval()/exec() with safer alternatives (JSON.parse for data, explicit function dispatch for logic).",
    module_reference="analysis.rules.ast_security.run_ast_security_rules",
))

_reg(RuleSpec(
    rule_id="SEC-AST-MISSING-ERRHANDLING",
    category="Security",
    name="Missing Error Handling",
    description="File imports I/O or network libraries but contains no try/catch or try/except block.",
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    cwe="CWE-703",
    resolution="Wrap I/O and network calls in try/catch blocks and handle or log exceptions explicitly.",
    module_reference="analysis.rules.ast_security.run_ast_security_rules",
))

# -- Metric findings (class_metrics.py) ---------------------------------------

_reg(RuleSpec(
    rule_id="METRIC-HIGH-WMC",
    category="Metrics",
    name="High WMC (public method count)",
    description="Class has more than 15 public methods (WMC proxy). May indicate too many responsibilities.",
    severity="High",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution="Apply the Single Responsibility Principle: split the class into smaller, focused classes.",
    module_reference="analysis.metrics.class_metrics.calculate_repo_averages",
))

_reg(RuleSpec(
    rule_id="METRIC-DEEP-DIT",
    category="Metrics",
    name="Deep Inheritance (DIT >= 3)",
    description="Class inheritance depth is 3 or more levels. Deep hierarchies are harder to trace and test.",
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution="Favour composition over deep inheritance. Consider flattening the hierarchy.",
    module_reference="analysis.metrics.class_metrics.calculate_repo_averages",
))

_reg(RuleSpec(
    rule_id="METRIC-LOW-COHESION",
    category="Metrics",
    name="Low Cohesion (LCOM proxy > 10)",
    description="LCOM proxy (methods - 1) exceeds 10, suggesting the class may do too many unrelated things.",
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution="Split the class along logical boundaries so each class has a single cohesive responsibility.",
    module_reference="analysis.metrics.class_metrics.calculate_repo_averages",
))

_reg(RuleSpec(
    rule_id="METRIC-HIGH-CBO",
    category="Metrics",
    name="High CBO (Coupling Between Objects)",
    description="File has 5 or more total dependency connections (in + out), making it fragile to changes.",
    severity="Medium",
    languages=(),
    resolution="Reduce coupling by extracting interfaces, applying dependency inversion, or splitting responsibilities.",
    module_reference="analysis.metrics.graph_metrics.detect_high_cbo",
))

# ---------------------------------------------------------------------------
# Phase 2 — Code Smell rules (CODE- prefix)
# ---------------------------------------------------------------------------

_reg(RuleSpec(
    rule_id="CODE-LONG-LINE",
    category="Code Smell",
    name="Long Line",
    description="A source line exceeds the configured maximum character threshold (default 100).",
    severity="Low",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution="Break long lines into multiple shorter lines for readability.",
    module_reference="analysis.rules.smells.line_length.check_line_length",
))

_reg(RuleSpec(
    rule_id="CODE-UNDEFINED-NAME",
    category="Code Smell",
    name="Undefined Name",
    description=(
        "An identifier is referenced but has no visible declaration in the file's scope. "
        "May indicate a typo, a missing import, or a copy-paste error."
    ),
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript"),
    resolution="Add the missing import or declaration. Check for typos in the identifier name.",
    module_reference="analysis.rules.smells.undefined_names",
))

_reg(RuleSpec(
    rule_id="CODE-UNUSED-VARIABLE",
    category="Code Smell",
    name="Unused Variable",
    description="A local variable is declared but never referenced within its scope.",
    severity="Low",
    languages=("Python", "JavaScript", "TypeScript", "Java"),
    resolution=(
        "Remove the unused variable, or prefix with _ if it is intentionally ignored. "
        "In Python, use _ for throw-away bindings."
    ),
    module_reference="analysis.rules.smells.unused_symbols",
))

_reg(RuleSpec(
    rule_id="CODE-UNUSED-ARGUMENT",
    category="Code Smell",
    name="Unused Argument",
    description="A function parameter is declared but never used inside the function body.",
    severity="Low",
    languages=("Python", "JavaScript", "TypeScript"),
    resolution=(
        "Remove the parameter if not needed, or prefix with _ to signal intentional discard. "
        "If required by an interface, document why it is unused."
    ),
    module_reference="analysis.rules.smells.unused_symbols",
))

_reg(RuleSpec(
    rule_id="CODE-TOO-FEW-PUBLIC-METHODS",
    category="Code Smell",
    name="Too Few Public Methods",
    description=(
        "A class has fewer public methods than the configured minimum (default 2). "
        "Very thin classes often should be plain functions or data structures instead."
    ),
    severity="Low",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution=(
        "Consider whether the class should be refactored to a function, "
        "named tuple, or dataclass. If the class is intentionally minimal, "
        "this finding can be suppressed."
    ),
    module_reference="analysis.rules.smells.public_methods.check_too_few_public_methods",
))

_reg(RuleSpec(
    rule_id="CODE-INCONSISTENT-RETURN",
    category="Code Smell",
    name="Inconsistent Return",
    description=(
        "A function has return statements that sometimes return a value and sometimes "
        "do not (bare return or fall-through). Callers cannot reliably use the return value."
    ),
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript"),
    resolution=(
        "Ensure all code paths return the same type. "
        "If the function is void/None-returning, remove the value-carrying returns."
    ),
    module_reference="analysis.rules.smells.returns",
))

_reg(RuleSpec(
    rule_id="CODE-FORMATTING",
    category="Code Smell",
    name="Formatting Anomaly",
    description=(
        "The file contains detectable formatting inconsistencies: "
        "mixed indentation (Python), trailing whitespace, or mixed brace style (JS/Java/C++)."
    ),
    severity="Low",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution=(
        "Run an auto-formatter (black/autopep8 for Python, prettier for JS/TS, "
        "clang-format for C++) and commit the formatting baseline."
    ),
    module_reference="analysis.rules.smells.formatting.check_formatting",
))

_reg(RuleSpec(
    rule_id="CODE-DUPLICATE-BLOCK",
    category="Code Smell",
    name="Duplicate Code Block",
    description=(
        "Two or more functions have structurally identical bodies (same node-type sequence "
        "after normalizing identifiers and literals). Copy-paste code increases maintenance burden."
    ),
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    resolution=(
        "Extract the shared logic into a shared helper function or utility module "
        "and call it from both locations."
    ),
    module_reference="analysis.rules.smells.duplicate_code.find_duplicates",
))


# ---------------------------------------------------------------------------
# Phase 3 — Security Smell / CWE rules (SEC- prefix, new structured engine)
# ---------------------------------------------------------------------------

_reg(RuleSpec(
    rule_id="SEC-CWE-502",
    category="Security",
    name="Unsafe Deserialization (CWE-502)",
    description=(
        "Use of an unsafe deserialization API that can execute arbitrary code "
        "when processing attacker-controlled data."
    ),
    severity="High",
    languages=("Python", "Java", "JavaScript", "TypeScript"),
    cwe="CWE-502",
    resolution=(
        "Replace pickle/marshal/yaml.load with safe alternatives: "
        "json, yaml.safe_load, or a schema-validated format. "
        "For Java, use serialization filters (Java 9+) or switch to JSON/Protobuf."
    ),
    autofix_available=True,   # Phase 5: Python yaml.load→yaml.safe_load (Tier 1)
    module_reference="analysis.rules.security.deserialization",
))

_reg(RuleSpec(
    rule_id="SEC-WEAK-CRYPTO",
    category="Security",
    name="Weak Cryptographic Hash (CWE-327)",
    description=(
        "Use of a cryptographically broken hash algorithm (MD5 or SHA-1) "
        "in a security-sensitive context."
    ),
    severity="Medium",
    languages=("Python", "Java", "JavaScript", "TypeScript", "C++"),
    cwe="CWE-327",
    resolution=(
        "Replace MD5/SHA-1 with SHA-256 (hashlib.sha256, SHA-256, crypto.createHash('sha256'), EVP_sha256). "
        "Note: if the hash is used only as a non-security checksum (e.g. cache key), "
        "this finding may be a false positive — document the intent."
    ),
    autofix_available=True,   # Phase 5: Python/Java/JS/TS hash algorithm substitution (Tier 1)
    module_reference="analysis.rules.security.weak_crypto",
))

_reg(RuleSpec(
    rule_id="SEC-UNSAFE-ASSERT",
    category="Security",
    name="Unsafe Assert as Security Boundary (CWE-617)",
    description=(
        "A Python assert statement appears to guard a security check. "
        "assert statements are disabled in optimized mode (python -O), "
        "making this check silently bypassable."
    ),
    severity="Medium",
    languages=("Python",),
    cwe="CWE-617",
    resolution=(
        "Replace the assert with an explicit conditional check and raise "
        "an appropriate exception (e.g. PermissionError, ValueError, HTTPException). "
        "Never rely on assert for authentication or authorization logic."
    ),
    autofix_available=False,
    module_reference="analysis.rules.security.unsafe_assert",
))

_reg(RuleSpec(
    rule_id="SEC-DANGEROUS-EXEC",
    category="Security",
    name="Dangerous Code/Command Execution (CWE-78 / CWE-95)",
    description=(
        "Use of an API that executes shell commands or evaluates code dynamically. "
        "Passing attacker-controlled input to these APIs leads to injection (CWE-78 or CWE-95)."
    ),
    severity="High",
    languages=("Python", "JavaScript", "TypeScript", "Java", "C++"),
    cwe="CWE-78",
    resolution=(
        "Avoid eval/exec. For shell execution, use subprocess.run() with a list argument "
        "and shell=False. Validate and sanitize all input before passing to any execution API."
    ),
    autofix_available=False,
    module_reference="analysis.rules.security.dangerous_exec",
))

_reg(RuleSpec(
    rule_id="SEC-CWE-703",
    category="Security",
    name="Missing Exception Handling for Risky Operation (CWE-703)",
    description=(
        "A potentially failing I/O, network, or system call is not enclosed in "
        "a try/catch block. Unhandled exceptions can crash the process, expose "
        "stack traces, or leave resources in an inconsistent state."
    ),
    severity="Medium",
    languages=("Python", "JavaScript", "TypeScript", "Java"),
    cwe="CWE-703",
    resolution=(
        "Wrap risky operations in try/except (Python) or try/catch (Java/JS/TS). "
        "Handle or log exceptions explicitly; avoid bare except clauses that swallow all errors."
    ),
    autofix_available=False,
    module_reference="analysis.rules.security.exception_handling",
))


def get(rule_id: str) -> Optional[RuleSpec]:
    """Look up a rule by its stable ID. Returns None if not found."""
    return RULE_REGISTRY.get(rule_id)


def all_rules() -> list[RuleSpec]:
    """Return all registered rules in insertion order."""
    return list(RULE_REGISTRY.values())

