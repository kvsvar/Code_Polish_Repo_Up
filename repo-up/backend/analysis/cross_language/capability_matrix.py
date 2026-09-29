"""
analysis/cross_language/capability_matrix.py
Phase 4 — Cross-Language Capability Matrix

Machine-readable record of per-rule, per-language implementation status.
Used by the parity test (validate_parity.py) to generate structured reports.

Status values
-------------
"full"    — AST-based, tested against fixture, line numbers supported
"partial" — AST-based but has known gaps (documented inline)
"text"    — Raw-text / regex scan (not AST-based), still useful
"stub"    — Function exists but returns empty / always passes
"none"    — Not implemented; architecture limitation documented
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

CAPABILITY_MATRIX: dict[str, dict] = {

    # =========================================================================
    # Phase 1 / structural rules
    # =========================================================================

    "STRUCT-MISSING-README": {
        "description": "Missing README.md in project root",
        "languages": {"all": "full"},
        "source_location": False,
        "confidence": "high",
        "notes": "File-system check — language-agnostic.",
    },
    "STRUCT-MISSING-LICENSE": {
        "description": "Missing LICENSE file",
        "languages": {"all": "full"},
        "source_location": False,
        "confidence": "high",
        "notes": "File-system check.",
    },
    "STRUCT-CIRCULAR-DEP": {
        "description": "Circular dependency detected via Tarjan SCC",
        "languages": {
            "Python":     "full",
            "JavaScript": "full",
            "TypeScript": "full",
            "Java":       "partial",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "high",
        "notes": (
            "Java: intra-package imports parsed; external jar dependencies not resolved. "
            "C++: #include paths normalized; system headers excluded."
        ),
    },

    # =========================================================================
    # Phase 1 / security rules (legacy, security.py)
    # =========================================================================

    "SEC-COMMITTED-ENV": {
        "description": "Committed .env file detected",
        "languages": {"all": "full"},
        "source_location": True,
        "confidence": "high",
        "notes": "File-system name match.",
    },
    "SEC-HARDCODED-SECRET": {
        "description": "Hardcoded credential detected",
        "languages": {"all": "text"},
        "source_location": True,
        "confidence": "medium",
        "notes": "Regex shape-based. No entropy scoring. All 7 patterns documented in secrets.py.",
    },

    # =========================================================================
    # Phase 3 / structured security rules
    # =========================================================================

    "SEC-CWE-502": {
        "description": "Unsafe deserialization (CWE-502)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "high",
        "notes": (
            "Python: pickle/marshal/shelve/yaml.load AST call detection. "
            "Java: readObject() method name match only (no type resolution). "
            "JS/TS: node-serialize import detection only. "
            "C++: no reliable static detection without full type resolution."
        ),
    },
    "SEC-WEAK-CRYPTO": {
        "description": "Weak cryptographic hash (CWE-327)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "high",
        "notes": (
            "Java: MessageDigest.getInstance() string arg match. "
            "C++: OpenSSL function name match only (EVP_md5, MD5_Init, etc.)."
        ),
    },
    "SEC-UNSAFE-ASSERT": {
        "description": "Assert used as security boundary (CWE-617 proxy)",
        "languages": {
            "Python":     "partial",
            "Java":       "none",
            "JavaScript": "none",
            "TypeScript": "none",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Python only. Heuristic keyword matching on assert test expression. "
            "Java/JS/TS/C++: assert semantics differ significantly; not implemented."
        ),
    },
    "SEC-DANGEROUS-EXEC": {
        "description": "Dangerous code/command execution (CWE-78/95)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "high",
        "notes": (
            "Java: Runtime.exec and ProcessBuilder.start() by name; no taint flow. "
            "C++: system/popen/exec* by function name; no taint flow."
        ),
    },
    "SEC-CWE-703": {
        "description": "Missing exception handling (CWE-703)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Checks syntactic enclosure in try block, not semantic coverage. "
            "Java: object_creation_expression for risky types only. "
            "C++: exception handling requires type resolution; not implemented."
        ),
    },

    # =========================================================================
    # Phase 2 / code smell rules
    # =========================================================================

    "CODE-LONG-LINE": {
        "description": "Source line exceeds 100-character threshold",
        "languages": {
            "Python":     "full",
            "Java":       "full",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "full",
        },
        "source_location": True,
        "confidence": "high",
        "notes": "Text scan; minified-file guard applied (>80% long lines = skip).",
    },
    "CODE-UNDEFINED-NAME": {
        "description": "Identifier referenced without visible declaration",
        "languages": {
            "Python":     "full",
            "Java":       "none",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Python: scope collects imports, builtins, params, locals. "
            "JS/TS: module-scope identifiers; dynamic require() not resolved. "
            "Java: class-level type resolution required; not implemented. "
            "C++: macro expansion and header inclusion make this infeasible."
        ),
    },
    "CODE-UNUSED-VARIABLE": {
        "description": "Variable declared but never referenced in scope",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Java: local variable detection only; field/class-level variables not tracked. "
            "C++: pointer arithmetic and macros make this unreliable."
        ),
    },
    "CODE-UNUSED-ARGUMENT": {
        "description": "Function parameter declared but never used",
        "languages": {
            "Python":     "full",
            "Java":       "none",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Java: overriding/implementing methods require parameters from interfaces; "
            "too many false positives without type resolution. "
            "C++: same reason."
        ),
    },
    "CODE-TOO-FEW-PUBLIC-METHODS": {
        "description": "Class has fewer than 2 public methods",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Reuses class_metrics.py output. "
            "Java: access modifiers parsed; inner-class distinction limited. "
            "C++: no public/private keyword enforcement on struct. "
            "JS/TS: private field # detection but no TypeScript access modifiers."
        ),
    },
    "CODE-INCONSISTENT-RETURN": {
        "description": "Function has mixed valued/bare returns",
        "languages": {
            "Python":     "full",
            "Java":       "none",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "none",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Java/C++: return type is declared; bare return is a type error, not a smell. "
            "These languages cannot have ambiguous returns by definition."
        ),
    },
    "CODE-FORMATTING": {
        "description": "Formatting inconsistency (mixed indent / brace style)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "low",
        "notes": (
            "Python: mixed tabs/spaces detection. "
            "Java/JS/TS/C++: K&R vs Allman brace detection; "
            "conservative threshold applied to reduce false positives."
        ),
    },
    "CODE-DUPLICATE-BLOCK": {
        "description": "Two functions have identical AST structural fingerprints",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": (
            "Uses normalized node-type hash (identifiers→ID, literals→LIT). "
            "Java: method_declaration body extraction. "
            "C++: function_definition body extraction; template bodies may FP."
        ),
    },

    # =========================================================================
    # Phase 1 / metric rules
    # =========================================================================

    "METRIC-HIGH-WMC": {
        "description": "Class has >15 public methods (WMC proxy)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": "Uses class_metrics.py. Java/C++ access modifier detection limited.",
    },
    "METRIC-DEEP-DIT": {
        "description": "Class has DIT >= 3",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "medium",
        "notes": "Inheritance depth counted by parse-time base class references only.",
    },
    "METRIC-LOW-COHESION": {
        "description": "Class has LCOM proxy > 10",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "partial",
            "TypeScript": "partial",
            "C++":        "partial",
        },
        "source_location": True,
        "confidence": "low",
        "notes": "LCOM proxy = methods − 1. Not true LCOM4 (no field access tracking).",
    },
    "METRIC-HIGH-CBO": {
        "description": "File has high coupling (in+out > 5)",
        "languages": {
            "Python":     "full",
            "Java":       "partial",
            "JavaScript": "full",
            "TypeScript": "full",
            "C++":        "partial",
        },
        "source_location": False,
        "confidence": "medium",
        "notes": "Graph-based. C++: system headers excluded from coupling count.",
    },
}


def get_language_support(rule_id: str, language: str) -> str:
    """Return support level for a specific rule+language combination."""
    entry = CAPABILITY_MATRIX.get(rule_id, {})
    langs = entry.get("languages", {})
    return langs.get(language) or langs.get("all", "none")


def get_supported_languages(rule_id: str) -> list[str]:
    """Return list of languages with non-'none' support for a rule."""
    entry = CAPABILITY_MATRIX.get(rule_id, {})
    langs = entry.get("languages", {})
    if "all" in langs:
        return ["Python", "JavaScript", "TypeScript", "Java", "C++"]
    return [lang for lang, status in langs.items() if status != "none"]


def render_matrix_table() -> str:
    """Render a plain-text capability matrix for reporting."""
    all_langs = ["Python", "JavaScript", "TypeScript", "Java", "C++"]
    header = f"{'Rule':<35} " + " ".join(f"{l[:5]:>8}" for l in all_langs)
    lines = [header, "-" * len(header)]
    for rule_id, entry in CAPABILITY_MATRIX.items():
        langs = entry.get("languages", {})
        row = f"{rule_id:<35} "
        for lang in all_langs:
            status = langs.get(lang) or langs.get("all", "none")
            abbr = {"full": "FULL", "partial": "PART", "text": "TEXT",
                    "stub": "STUB", "none": "----"}.get(status, "????")
            row += f"{abbr:>8} "
        lines.append(row)
    return "\n".join(lines)
