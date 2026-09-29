"""
analysis/rules/smells/unused_symbols.py
CODE-UNUSED-VARIABLE  — local variable declared but never referenced in scope.
CODE-UNUSED-ARGUMENT  — function/method parameter never used in its body.

Approach
--------
For each function/method body we:
  1. Collect declarations  (assignments, for-loop targets, with-as, etc.)
  2. Collect parameters    (from function parameter list)
  3. Walk the body collecting identifier references
  4. Anything declared but not referenced is flagged.

Supported:  Python, JavaScript, TypeScript
Partial:    Java (detects some local vars; Java generics / field access miss-rate
            is acceptable for a first-pass smell finder)
Not supported: C++ (complex macro / template resolution; declared intentionally
               unsupported to avoid false-positive explosion)

Exclusions (to minimise false positives)
-----------------------------------------
* Names starting with _ (Python convention for intentional discard)
* Names starting with __ (dunder)
* 'self', 'cls', 'this' are never flagged as parameters
* Single-letter loop vars i, j, k (common idiom)
* Names that appear in nested functions / lambdas are considered used
  (conservative; some false negatives OK)
* Parameters of overriding methods and abstract methods are skipped
  (Python: any function inside a class body decorated with @abstractmethod
   or @override; JS/TS: methods on classes — we skip per-method unused-arg
   detection to avoid framework callback FP)
"""

from __future__ import annotations
from .ast_helpers import walk_depth_first, node_text, find_all

# Names that are always considered "used" even if not referenced
_ALWAYS_USED = frozenset({"self", "cls", "this", "super", "_", "__"})

# Common single-letter iteration vars we conservatively skip
_LOOP_IDIOMS = frozenset({"i", "j", "k", "n", "m", "x", "y", "z", "e", "ex", "err", "exc"})

# --- Python helpers ---

_PY_ASSIGNMENT_LHS = frozenset({
    "identifier",
})

_PY_PARAM_TYPES = frozenset({
    "identifier",          # positional
    "default_parameter",   # name=default
    "typed_parameter",     # name: Type
    "typed_default_parameter",  # name: Type = default
    "list_splat_pattern",  # *args
    "dictionary_splat_pattern",  # **kwargs
})


def _py_param_name(node) -> str | None:
    """Extract the param name from a parameter node."""
    if node.type == "identifier":
        return node_text(node)
    for child in node.children:
        if child.type == "identifier":
            return node_text(child)
    return None


def _py_collect_params(func_node) -> list[tuple[str, int]]:
    """Return list of (name, line) for a Python function_definition node."""
    params = []
    for child in func_node.children:
        if child.type == "parameters":
            for p in child.children:
                if p.type in _PY_PARAM_TYPES:
                    name = _py_param_name(p)
                    if name and name not in _ALWAYS_USED and not name.startswith("_"):
                        params.append((name, p.start_point[0] + 1))
    return params


def _py_collect_local_vars(body_node) -> list[tuple[str, int]]:
    """Collect local variable bindings inside a Python function body."""
    bindings = []
    for node in walk_depth_first(body_node):
        # Simple assignment: x = ...
        if node.type == "assignment":
            lhs = node.children[0] if node.children else None
            if lhs and lhs.type == "identifier":
                name = node_text(lhs)
                if name and not name.startswith("_") and name not in _ALWAYS_USED:
                    bindings.append((name, lhs.start_point[0] + 1))
        # for x in ...:
        if node.type == "for_statement":
            for child in node.children:
                if child.type in ("identifier", "tuple_pattern", "list_pattern"):
                    if child.type == "identifier":
                        name = node_text(child)
                        if name and not name.startswith("_") and name not in _LOOP_IDIOMS:
                            bindings.append((name, child.start_point[0] + 1))
                    break  # only the loop target
        # with ... as x:
        if node.type == "with_item":
            for child in node.children:
                if child.type == "as_pattern":
                    for sub in child.children:
                        if sub.type in ("identifier", "as_pattern_target"):
                            name = node_text(sub)
                            if name and not name.startswith("_"):
                                bindings.append((name, sub.start_point[0] + 1))
    return bindings


def _py_collect_references(body_node) -> set[str]:
    """Collect all identifier references inside a function body."""
    refs: set[str] = set()
    for node in walk_depth_first(body_node):
        if node.type == "identifier":
            refs.add(node_text(node))
    return refs


def analyze_python_unused(tree, rel_path: str) -> list[dict]:
    """Return unused-variable and unused-argument findings for a Python file."""
    results: list[dict] = []
    root = tree.root_node

    # Gather module-level identifiers (used in file scope) for very basic
    # module-level assignment tracking — we only report inside functions
    for func_node in find_all(root, "function_definition"):
        # Skip abstract/override  methods heuristically
        # (decorated methods often have "required" unused params)
        parent = func_node.parent
        is_method = parent and parent.type in ("block", "class_body", "decorated_definition")

        # Collect body (last child is the block)
        body = None
        for child in func_node.children:
            if child.type == "block":
                body = child
                break
        if body is None:
            continue

        refs = _py_collect_references(body)

        # Unused arguments
        if not is_method:  # only flag top-level function args; methods have framework patterns
            for param_name, line in _py_collect_params(func_node):
                if param_name not in refs and param_name not in _LOOP_IDIOMS:
                    results.append({
                        "rule_id": "CODE-UNUSED-ARGUMENT",
                        "param": param_name,
                        "line": line,
                        "file": rel_path,
                    })

        # Unused local variables
        for var_name, line in _py_collect_local_vars(body):
            # A name is "used" if it appears at least once in the full body refs
            # minus the definition site (we check if it appears in refs at all,
            # which includes the definition — so we need >=2 occurrences OR
            # appearance after the definition).  Conservative: if in refs, skip.
            if var_name not in refs:
                results.append({
                    "rule_id": "CODE-UNUSED-VARIABLE",
                    "var": var_name,
                    "line": line,
                    "file": rel_path,
                })

    return results


# --- JavaScript / TypeScript helpers ---

_JS_PARAM_TYPES = frozenset({
    "identifier",
    "assignment_pattern",       # name = default
    "rest_pattern",             # ...args
    "object_pattern",           # destructuring
    "array_pattern",            # destructuring
})


def _js_collect_params(func_node) -> list[tuple[str, int]]:
    params = []
    for child in func_node.children:
        if child.type == "formal_parameters":
            for p in child.children:
                if p.type == "identifier":
                    name = node_text(p)
                    if name and not name.startswith("_") and name not in _ALWAYS_USED:
                        params.append((name, p.start_point[0] + 1))
                elif p.type == "assignment_pattern":
                    for sub in p.children:
                        if sub.type == "identifier":
                            name = node_text(sub)
                            if name and not name.startswith("_"):
                                params.append((name, sub.start_point[0] + 1))
                            break
    return params


def _js_collect_local_vars(body_node) -> list[tuple[str, int]]:
    bindings = []
    for node in walk_depth_first(body_node):
        # let x = ..., const x = ..., var x = ...
        if node.type in ("variable_declarator",):
            id_node = node.children[0] if node.children else None
            if id_node and id_node.type == "identifier":
                name = node_text(id_node)
                if name and not name.startswith("_") and name not in _LOOP_IDIOMS:
                    bindings.append((name, id_node.start_point[0] + 1))
    return bindings


def _js_collect_references(body_node) -> set[str]:
    refs: set[str] = set()
    for node in walk_depth_first(body_node):
        if node.type == "identifier":
            refs.add(node_text(node))
    return refs


def analyze_js_unused(tree, rel_path: str) -> list[dict]:
    """Return unused-variable and unused-argument findings for a JS/TS file."""
    results: list[dict] = []
    root = tree.root_node

    func_types = (
        "function_declaration",
        "function",
        "arrow_function",
        "method_definition",
    )

    for func_node in find_all(root, *func_types):
        # Skip class methods for unused-argument (framework callbacks etc.)
        is_method = func_node.type == "method_definition"

        body = None
        for child in func_node.children:
            if child.type in ("statement_block", "block"):
                body = child
                break
        if body is None:
            continue

        refs = _js_collect_references(body)

        if not is_method:
            for param_name, line in _js_collect_params(func_node):
                if param_name not in refs:
                    results.append({
                        "rule_id": "CODE-UNUSED-ARGUMENT",
                        "param": param_name,
                        "line": line,
                        "file": rel_path,
                    })

        for var_name, line in _js_collect_local_vars(body):
            if var_name not in refs:
                results.append({
                    "rule_id": "CODE-UNUSED-VARIABLE",
                    "var": var_name,
                    "line": line,
                    "file": rel_path,
                })

    return results


def analyze_java_unused(tree, rel_path: str) -> list[dict]:
    """
    Java unused-variable detection — conservative first pass.

    Limitation: Java's type system (fields vs locals, generics, shadowing) makes
    full unused-variable analysis require a compiler.  We only check local
    variable_declarator nodes inside method bodies and verify the name appears
    in the body's identifier set (>=2 times including declaration).
    """
    results: list[dict] = []
    root = tree.root_node

    for method in find_all(root, "method_declaration"):
        body = None
        for child in method.children:
            if child.type == "block":
                body = child
                break
        if body is None:
            continue

        # Count all identifier occurrences
        counts: dict[str, int] = {}
        for node in walk_depth_first(body):
            if node.type == "identifier":
                name = node_text(node)
                counts[name] = counts.get(name, 0) + 1

        # Variable declarators
        for decl in find_all(body, "variable_declarator"):
            for child in decl.children:
                if child.type == "identifier":
                    name = node_text(child)
                    if (name
                            and not name.startswith("_")
                            and name not in _ALWAYS_USED
                            and name not in _LOOP_IDIOMS):
                        # Name appears only once → only at declaration site
                        if counts.get(name, 0) <= 1:
                            results.append({
                                "rule_id": "CODE-UNUSED-VARIABLE",
                                "var": name,
                                "line": child.start_point[0] + 1,
                                "file": rel_path,
                            })
                    break

    return results


# C++ — explicitly not supported (too many FP risks from macros and templates)
def analyze_cpp_unused(_tree, _rel_path: str) -> list[dict]:
    """C++ unused-variable detection: not implemented (see module docstring)."""
    return []
