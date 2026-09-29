"""
analysis/rules/smells/undefined_names.py
CODE-UNDEFINED-NAME — Reference to a name that has no visible declaration.

Approach
--------
Scope-aware: we build a flat scope for each file (module/global level + the
enclosing function) and check each identifier reference against:
  1. Built-in names for the language
  2. Module-level declarations (imports, function defs, class defs, assignments)
  3. Local declarations in the enclosing function

This is a FIRST-PASS smell finder, not a compiler.  The following are
intentionally excluded to keep false-positive rates acceptable:
  - Attribute accesses (a.b — we only flag standalone identifiers)
  - Names that appear in a call_expression callee position within a member
    expression (methods on objects)
  - Any name that appears as a type annotation (too many framework generics)
  - Names that appear on the LHS of a member_expression / attribute
  - All names resolved in imported namespaces (we track the alias, not the
    namespace members)

Supported: Python (most accurate), JavaScript/TypeScript (good), Java (limited)
Not supported: C++ (linker-level resolution not feasible via AST alone)

Known false-negative sources
-----------------------------
* Dynamic attribute access (getattr, obj.__dict__)
* Star imports (from foo import *)
* Conditional imports (try: import X except: X = None)
* Decorator names (we include them in module scope to avoid FP)
"""

from __future__ import annotations
from .ast_helpers import walk_depth_first, node_text, find_all

# ---------------------------------------------------------------------------
# Language built-ins
# ---------------------------------------------------------------------------

_PY_BUILTINS = frozenset({
    # functions
    "print", "len", "range", "enumerate", "zip", "map", "filter", "sorted",
    "reversed", "list", "dict", "set", "tuple", "str", "int", "float",
    "bool", "bytes", "bytearray", "type", "isinstance", "issubclass",
    "hasattr", "getattr", "setattr", "delattr", "callable", "repr", "abs",
    "round", "min", "max", "sum", "all", "any", "open", "input", "print",
    "vars", "dir", "id", "hash", "hex", "oct", "bin", "chr", "ord",
    "format", "iter", "next", "object", "super", "staticmethod",
    "classmethod", "property", "staticmethod", "NotImplemented",
    "NotImplementedError",
    # exceptions
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
    "AttributeError", "RuntimeError", "StopIteration", "GeneratorExit",
    "SystemExit", "KeyboardInterrupt", "OverflowError", "ZeroDivisionError",
    "IOError", "OSError", "FileNotFoundError", "PermissionError",
    "ImportError", "ModuleNotFoundError", "NameError", "UnboundLocalError",
    "AssertionError", "NotImplementedError", "RecursionError",
    # constants
    "True", "False", "None", "Ellipsis", "__name__", "__file__",
    "__doc__", "__package__", "__spec__", "__loader__", "__builtins__",
    "__all__", "__slots__", "__dict__", "__class__", "__init__",
    "__repr__", "__str__", "__len__", "__iter__", "__next__",
    # typing
    "Optional", "List", "Dict", "Tuple", "Set", "Union", "Any",
    "Callable", "Generator", "Iterator", "Iterable", "Sequence",
    "Mapping", "ClassVar", "Final", "Literal", "TypeVar", "Generic",
    "Protocol", "overload", "dataclass", "field",
    # common stdlib that appear without import in context
    "self", "cls",
})

_JS_GLOBALS = frozenset({
    "console", "window", "document", "process", "global", "globalThis",
    "module", "exports", "require", "import", "__dirname", "__filename",
    "setTimeout", "clearTimeout", "setInterval", "clearInterval",
    "Promise", "async", "await", "undefined", "null", "NaN", "Infinity", "eval",
    "JSON", "Math", "Date", "Array", "Object", "String", "Number",
    "Boolean", "Symbol", "RegExp", "Error", "TypeError", "RangeError",
    "fetch", "URL", "URLSearchParams",
    "React", "useState", "useEffect", "useRef", "useCallback", "useMemo",
    # Node globals
    "Buffer", "EventEmitter",
    # Test globals
    "describe", "it", "test", "expect", "beforeEach", "afterEach",
    "beforeAll", "afterAll", "jest",
    "this",
})

_JAVA_GLOBALS = frozenset({
    "System", "String", "Integer", "Long", "Double", "Float", "Boolean",
    "Object", "Class", "Math", "Arrays", "Collections", "List", "ArrayList",
    "HashMap", "Map", "Set", "HashSet", "Iterator", "Optional",
    "Override", "Deprecated", "SuppressWarnings",
    "NullPointerException", "IllegalArgumentException", "RuntimeException",
    "Exception", "Throwable", "Error",
    "this", "super", "null", "true", "false",
    "void", "int", "long", "double", "float", "boolean", "char", "byte", "short",
})


# ---------------------------------------------------------------------------
# Python: module-scope declaration collection
# ---------------------------------------------------------------------------

def _py_module_scope(root) -> set[str]:
    """Collect all top-level declared names in a Python module."""
    names: set[str] = set(_PY_BUILTINS)
    for node in root.children:
        # import X / import X as Y
        if node.type == "import_statement":
            for child in walk_depth_first(node):
                if child.type in ("dotted_name", "identifier"):
                    # take the last part (alias or last component)
                    names.add(node_text(child).split(".")[-1])
        # from X import Y / from X import Y as Z
        elif node.type == "import_from_statement":
            for child in node.children:
                if child.type == "import_list":
                    for imp in child.children:
                        if imp.type == "aliased_import":
                            # 'X as Y' → add Y (the alias)
                            for sub in imp.children:
                                if sub.type == "identifier":
                                    names.add(node_text(sub))
                        elif imp.type == "identifier":
                            names.add(node_text(imp))
                elif child.type == "wildcard_import":
                    # star import — we cannot know what names come in;
                    # add a sentinel so we disable the rule for this file
                    names.add("*STAR*")
        # function/class definitions
        elif node.type in ("function_definition", "class_definition", "decorated_definition"):
            for child in node.children:
                if child.type in ("identifier", "name"):
                    names.add(node_text(child))
                    break
        # assignments (x = ..., x: T = ...)
        elif node.type in ("assignment", "augmented_assignment",
                            "annotated_assignment"):
            lhs = node.children[0] if node.children else None
            if lhs and lhs.type == "identifier":
                names.add(node_text(lhs))
        # TYPE_ALIAS / type statements (Python 3.12+)
        elif node.type == "type_alias_statement":
            for child in node.children:
                if child.type == "identifier":
                    names.add(node_text(child))
                    break
    return names


def _py_all_locals(root) -> set[str]:
    names: set[str] = set()
    for node in walk_depth_first(root):
        if node.type == "parameters":
            for p in node.children:
                if p.type == "identifier":
                    names.add(node_text(p))
                elif p.type in ("default_parameter", "typed_parameter", "typed_default_parameter"):
                    for sub in walk_depth_first(p):
                        if sub.type == "identifier":
                            names.add(node_text(sub))
                            break
        elif node.type == "assignment":
            lhs = node.children[0] if node.children else None
            if lhs and lhs.type == "identifier":
                names.add(node_text(lhs))
        elif node.type == "for_statement":
            for child in node.children:
                if child.type == "identifier":
                    names.add(node_text(child))
                    break
        elif node.type == "with_item":
            for child in node.children:
                if child.type == "as_pattern":
                    for sub in child.children:
                        if sub.type in ("identifier", "as_pattern_target"):
                            names.add(node_text(sub))
    return names

def analyze_python_undef(tree, rel_path: str) -> list[dict]:
    """Return CODE-UNDEFINED-NAME findings for a Python file."""
    root = tree.root_node
    scope = _py_module_scope(root)
    
    # Add local bindings to scope to avoid FP
    scope.update(_py_all_locals(root))

    # If a star-import exists we cannot reliably detect undefined names
    if "*STAR*" in scope:
        return []

    results: list[dict] = []
    seen: set[tuple] = set()

    # Walk entire tree; only flag identifiers that are:
    # 1. Not in scope
    # 2. Not in attribute position (parent.type == attribute & not first child)
    # 3. Not a keyword / type annotation
    _skip_parent_types = frozenset({
        "attribute",             # a.b  — skip 'b'
        "import_statement",
        "import_from_statement",
        "dotted_name",
        "keyword_argument",
        "function_definition",   # function name itself
        "class_definition",      # class name itself
        "parameters",
        "default_parameter",
        "typed_parameter",
        "typed_default_parameter",
        "assignment",            # LHS of assignment
        "augmented_assignment",
        "annotated_assignment",
        "type_annotation",
        "decorator",
        "for_in_clause",
    })

    def _in_attribute_rhs(node) -> bool:
        """True if this identifier is on the right side of an attribute access."""
        p = node.parent
        if p and p.type == "attribute":
            children = p.children
            for idx, c in enumerate(children):
                if c == node and idx > 0:
                    return True
        return False

    for node in walk_depth_first(root):
        if node.type != "identifier":
            continue
        name = node_text(node)
        if not name or name in scope:
            continue
        parent = node.parent
        if parent and parent.type in _skip_parent_types:
            continue
        if _in_attribute_rhs(node):
            continue
        # Skip type annotation identifiers
        gp = parent.parent if parent else None
        if gp and gp.type in ("type_annotation",):
            continue

        key = (rel_path, name, node.start_point[0] + 1)
        if key not in seen:
            seen.add(key)
            results.append({
                "rule_id": "CODE-UNDEFINED-NAME",
                "name": name,
                "line": node.start_point[0] + 1,
                "file": rel_path,
            })

    return results


# ---------------------------------------------------------------------------
# JS / TypeScript: module-scope declaration collection
# ---------------------------------------------------------------------------

def _js_module_scope(root) -> set[str]:
    names: set[str] = set(_JS_GLOBALS)
    for node in root.children:
        # import { X } from '...' / import X from '...'
        if node.type == "import_statement":
            for child in walk_depth_first(node):
                if child.type == "identifier":
                    names.add(node_text(child))
        # function foo() {}
        elif node.type in ("function_declaration", "generator_function_declaration"):
            for child in node.children:
                if child.type == "identifier":
                    names.add(node_text(child))
                    break
        # class Foo {}
        elif node.type == "class_declaration":
            for child in node.children:
                if child.type == "identifier":
                    names.add(node_text(child))
                    break
        # const/let/var x = ...
        elif node.type in ("lexical_declaration", "variable_declaration"):
            for child in walk_depth_first(node):
                if child.type == "identifier":
                    names.add(node_text(child))
        # export ...
        elif node.type in ("export_statement", "export_default_declaration"):
            for child in walk_depth_first(node):
                if child.type == "identifier":
                    names.add(node_text(child))
    return names


def _js_all_locals(root) -> set[str]:
    names: set[str] = set()
    for node in walk_depth_first(root):
        if node.type in ("formal_parameters", "lexical_declaration", "variable_declaration", "catch_clause"):
            for child in walk_depth_first(node):
                if child.type == "identifier":
                    names.add(node_text(child))
    return names


def analyze_js_undef(tree, rel_path: str) -> list[dict]:
    """Return CODE-UNDEFINED-NAME findings for a JS/TS file.

    Limitation: very conservative — only flags standalone identifiers that are
    not in module scope. Member-access RHS identifiers are skipped.
    """
    root = tree.root_node
    scope = _js_module_scope(root)
    scope.update(_js_all_locals(root))
    results: list[dict] = []
    seen: set[tuple] = set()

    _skip_parent_types = frozenset({
        "member_expression",     # a.b
        "import_specifier",
        "import_clause",
        "import_statement",
        "export_specifier",
        "export_statement",
        "function_declaration",
        "class_declaration",
        "method_definition",
        "property_identifier",
        "shorthand_property_identifier",
        "shorthand_property_identifier_pattern",
        "type_annotation",
        "type_identifier",
        "labeled_statement",
    })

    def _is_member_rhs(node) -> bool:
        p = node.parent
        if p and p.type == "member_expression":
            children = [c for c in p.children if c.type != "."]
            return len(children) >= 2 and children[-1] == node
        return False

    for node in walk_depth_first(root):
        if node.type != "identifier":
            continue
        name = node_text(node)
        if not name or name in scope:
            continue
        parent = node.parent
        if parent and parent.type in _skip_parent_types:
            continue
        if _is_member_rhs(node):
            continue

        key = (rel_path, name, node.start_point[0] + 1)
        if key not in seen:
            seen.add(key)
            results.append({
                "rule_id": "CODE-UNDEFINED-NAME",
                "name": name,
                "line": node.start_point[0] + 1,
                "file": rel_path,
            })

    return results


def analyze_java_undef(_tree, _rel_path: str) -> list[dict]:
    """Java undefined-name detection: not implemented.

    Java requires type resolution to distinguish fields vs. unresolved names.
    Returning empty to avoid false-positive explosion.
    """
    return []


def analyze_cpp_undef(_tree, _rel_path: str) -> list[dict]:
    """C++ undefined-name detection: not implemented (see module docstring)."""
    return []
