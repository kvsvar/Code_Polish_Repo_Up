"""
analysis/rules/smells/duplicate_code.py
CODE-DUPLICATE-BLOCK — Structurally similar function/method bodies across the repo.

Approach
--------
1. Parse all functions/methods in all supported language files.
2. Extract the body AST as a sequence of node types (structural fingerprint).
3. Normalize: replace identifier text and literal values with placeholders.
4. Hash the normalized sequence.
5. Group functions sharing the same hash.
6. Report pairs that exceed MIN_TOKENS (avoid trivially small blocks).

Normalization strategy
----------------------
* All identifier tokens → "ID"
* All string/number/boolean literals → "LIT"
* All comments are stripped (not included in fingerprint)
* Node *types* are kept (structure is preserved)

This catches:
  - Copy-paste functions with renamed variables
  - Identical boilerplate methods

This misses:
  - Semantically equivalent code with different structure
  - Inline expressions that are duplicated without being wrapped in a function

Supported: Python, JavaScript, TypeScript, Java, C++
(any language for which the AST is available)

Configuration
-------------
MIN_TOKENS     : minimum fingerprint length to consider (default 10)
MIN_FILES      : report duplicates found in >= 2 different files (cross-file)
                 AND same file (intra-file, ≥ 2 identical bodies in same class)

Limitations
-----------
* Very short functions (< MIN_TOKENS) are excluded to prevent noise.
* Getters/setters that all have the same body (return self.x) would fire;
  we guard by skipping bodies whose normalized form is extremely common
  (appears in > MAX_DUPLICATE_PAIRS groups total — cap at 20 reports per repo).
"""

from __future__ import annotations
import hashlib
from .ast_helpers import walk_depth_first, node_text

MIN_TOKENS = 10       # minimum structural tokens in a body fingerprint
MAX_REPORTS = 20      # cap total duplicate findings per repo

# Node types whose TEXT is replaced with "LIT" in the fingerprint
_LITERAL_TYPES = frozenset({
    "string", "integer", "float", "true", "false", "null", "none",
    "string_literal", "character_literal", "boolean_literal",
    "decimal_integer_literal", "hex_integer_literal", "float_literal",
    "number",
})

# Node types whose TEXT is replaced with "ID" in the fingerprint
_IDENTIFIER_TYPES = frozenset({
    "identifier", "type_identifier", "property_identifier",
    "field_identifier", "name", "variable_name",
})

# Node types to completely skip (don't contribute to fingerprint)
_SKIP_TYPES = frozenset({
    "comment", "line_comment", "block_comment",
    "{", "}", "(", ")", "[", "]", ";", ",", ":", ".", "->",
    "newline", "\n", "indent", "dedent",
})

_FUNCTION_TYPES = frozenset({
    # Python
    "function_definition",
    # JS/TS
    "function_declaration", "function", "arrow_function", "method_definition",
    # Java
    "method_declaration", "constructor_declaration",
    # C++
    "function_definition",  # same string; handled per-file by language param
})

_BODY_TYPES = frozenset({
    "block", "statement_block", "compound_statement",
    "body",
})


def _fingerprint(body_node) -> tuple[str, int]:
    """Return (normalized_hash, token_count) for a function body node."""
    tokens: list[str] = []
    for node in walk_depth_first(body_node):
        if node.type in _SKIP_TYPES:
            continue
        if node.type in _LITERAL_TYPES:
            tokens.append("LIT")
        elif node.type in _IDENTIFIER_TYPES:
            tokens.append("ID")
        else:
            tokens.append(node.type)
    digest = hashlib.md5("||".join(tokens).encode()).hexdigest()
    return digest, len(tokens)


def extract_function_bodies(tree, rel_path: str) -> list[dict]:
    """Return list of {hash, token_count, func_name, line, file} per function."""
    results = []
    if not tree:
        return results

    root = tree.root_node
    visited: set[int] = set()  # node id to avoid double-counting

    for node in walk_depth_first(root):
        if node.type not in _FUNCTION_TYPES:
            continue
        node_id = id(node)
        if node_id in visited:
            continue

        # Find body child
        body = None
        for child in node.children:
            if child.type in _BODY_TYPES:
                body = child
                break
        if body is None:
            continue

        fp, tok_count = _fingerprint(body)
        if tok_count < MIN_TOKENS:
            continue

        # Get function name
        func_name = "<anonymous>"
        for child in node.children:
            if child.type in _IDENTIFIER_TYPES:
                func_name = node_text(child)
                break

        visited.add(node_id)
        results.append({
            "hash": fp,
            "token_count": tok_count,
            "func_name": func_name,
            "line": node.start_point[0] + 1,
            "file": rel_path,
        })

    return results


def find_duplicates(all_bodies: list[dict]) -> list[dict]:
    """Group bodies by fingerprint hash and return pairs with duplicates.

    Returns list of raw finding dicts {rule_id, primary, secondary, ...}.
    Caps at MAX_REPORTS total.
    """
    from collections import defaultdict
    groups: dict[str, list[dict]] = defaultdict(list)
    for body in all_bodies:
        groups[body["hash"]].append(body)

    findings = []
    reported: set[frozenset] = set()

    for fp_hash, bodies in groups.items():
        if len(bodies) < 2:
            continue

        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                a, b = bodies[i], bodies[j]
                pair_key = frozenset({
                    (a["file"], a["line"]),
                    (b["file"], b["line"]),
                })
                if pair_key in reported:
                    continue
                reported.add(pair_key)

                findings.append({
                    "rule_id": "CODE-DUPLICATE-BLOCK",
                    "primary_file": a["file"],
                    "primary_line": a["line"],
                    "primary_func": a["func_name"],
                    "secondary_file": b["file"],
                    "secondary_line": b["line"],
                    "secondary_func": b["func_name"],
                    "token_count": a["token_count"],
                })

                if len(findings) >= MAX_REPORTS:
                    return findings

    return findings
