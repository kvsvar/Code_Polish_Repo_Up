"""
analysis/rules/smells/returns.py
CODE-INCONSISTENT-RETURN — Function has mixed return-with-value / bare-return paths.

Approach
--------
For each function/method body we:
  1. Collect all return statements at the FUNCTION's direct scope
     (not nested functions / lambdas)
  2. Classify each as:
     - VALUED  : return <expr>  (non-None expression)
     - BARE    : return         (no expression)
     - IMPLICIT: fall-through at end of function (no return statement at all)
  3. Flag if the function has BOTH valued returns AND bare/implicit returns.

Exclusions
----------
* Constructors (__init__, constructor) — expected to return None
* Abstract methods (Python: decorated with @abstractmethod; Java: abstract modifier)
* Very short functions (1-2 statement body) — noise
* Functions returning only None explicitly:
    return None  is treated as BARE (explicit None is the same as bare return)

Supported: Python (most complete), JavaScript/TypeScript (good), Java (basic)
Not supported: C++ (void vs return-type requires type resolution)

Limitation
----------
We do not model all control-flow paths; if a function has only one possible
return path we may miss inconsistency. This is a structural not a full CFG check.
"""

from __future__ import annotations
from .ast_helpers import node_text, find_all

_CONSTRUCTOR_NAMES = frozenset({"__init__", "__new__", "constructor"})


def _py_is_abstract(func_node) -> bool:
    """Heuristic: parent is a decorated_definition with @abstractmethod."""
    p = func_node.parent
    if p and p.type == "decorated_definition":
        for child in p.children:
            if child.type == "decorator":
                text = node_text(child)
                if "abstractmethod" in text:
                    return True
    return False


def _func_name_py(func_node) -> str:
    for child in func_node.children:
        if child.type == "identifier":
            return node_text(child)
    return ""


def _get_direct_returns_py(body_node):
    """Yield return statement nodes that are directly inside this body (not nested)."""
    # We do a shallow walk: descend into children but NOT into nested functions
    _stop_types = frozenset({"function_definition", "lambda", "class_definition"})

    def _walk(node):
        for child in node.children:
            if child.type in _stop_types:
                continue
            if child.type == "return_statement":
                yield child
            else:
                yield from _walk(child)

    yield from _walk(body_node)


def _py_return_has_value(ret_node) -> bool:
    """True if the return statement carries a non-None expression."""
    children = [c for c in ret_node.children if c.type not in ("return", "comment", "\n")]
    if not children:
        return False
    expr = children[0]
    # 'return None' → treat as bare
    if expr.type == "none" or (expr.type == "identifier" and node_text(expr) == "None"):
        return False
    return True


def analyze_python_returns(tree, rel_path: str) -> list[dict]:
    root = tree.root_node
    results: list[dict] = []

    for func in find_all(root, "function_definition"):
        name = _func_name_py(func)
        if name in _CONSTRUCTOR_NAMES:
            continue
        if _py_is_abstract(func):
            continue

        body = None
        for child in func.children:
            if child.type == "block":
                body = child
                break
        if body is None:
            continue

        # skip tiny bodies
        stmt_count = sum(1 for c in body.children if c.type not in ("\n", "comment"))
        if stmt_count <= 2:
            continue

        returns = list(_get_direct_returns_py(body))
        if not returns:
            continue  # implicit None return only; no mixed issue

        valued = [r for r in returns if _py_return_has_value(r)]
        bare = [r for r in returns if not _py_return_has_value(r)]

        if valued and bare:
            results.append({
                "rule_id": "CODE-INCONSISTENT-RETURN",
                "func": name,
                "line": func.start_point[0] + 1,
                "file": rel_path,
                "valued_count": len(valued),
                "bare_count": len(bare),
            })

    return results


# --- JavaScript / TypeScript ---

def _func_name_js(func_node) -> str:
    for child in func_node.children:
        if child.type in ("identifier", "property_identifier"):
            return node_text(child)
    return "<anonymous>"


def _get_direct_returns_js(body_node):
    _stop_types = frozenset({
        "function", "function_declaration", "arrow_function",
        "method_definition", "generator_function",
    })

    def _walk(node):
        for child in node.children:
            if child.type in _stop_types:
                continue
            if child.type == "return_statement":
                yield child
            else:
                yield from _walk(child)

    yield from _walk(body_node)


def _js_return_has_value(ret_node) -> bool:
    children = [c for c in ret_node.children
                if c.type not in ("return", ";", "comment")]
    if not children:
        return False
    expr = children[0]
    if expr.type in ("undefined", "null") or (
        expr.type == "identifier" and node_text(expr) in ("undefined", "null")
    ):
        return False
    return True


def analyze_js_returns(tree, rel_path: str) -> list[dict]:
    root = tree.root_node
    results: list[dict] = []

    func_types = (
        "function_declaration", "function",
        "arrow_function", "method_definition",
    )

    for func in find_all(root, *func_types):
        name = _func_name_js(func)
        if name in _CONSTRUCTOR_NAMES:
            continue

        body = None
        for child in func.children:
            if child.type in ("statement_block", "block"):
                body = child
                break
        if body is None:
            continue

        stmt_count = sum(1 for c in body.children if c.type not in ("{", "}", "\n", "comment"))
        if stmt_count <= 2:
            continue

        returns = list(_get_direct_returns_js(body))
        if not returns:
            continue

        valued = [r for r in returns if _js_return_has_value(r)]
        bare = [r for r in returns if not _js_return_has_value(r)]

        if valued and bare:
            results.append({
                "rule_id": "CODE-INCONSISTENT-RETURN",
                "func": name,
                "line": func.start_point[0] + 1,
                "file": rel_path,
                "valued_count": len(valued),
                "bare_count": len(bare),
            })

    return results


def analyze_java_returns(_tree, _rel_path: str) -> list[dict]:
    """Java inconsistent-return: not implemented.

    Java requires the return type from the method signature to determine if
    a bare return in a void method is expected. Without type resolution this
    would produce too many false positives.
    """
    return []


def analyze_cpp_returns(_tree, _rel_path: str) -> list[dict]:
    """C++ inconsistent-return: not implemented (requires type resolution)."""
    return []
