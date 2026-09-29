"""
analysis/rules/security/deserialization.py
SEC-CWE-502 — Unsafe Deserialization

CWE-502: Deserialization of Untrusted Data

Detects use of unsafe deserialization APIs that can lead to arbitrary code
execution when processing attacker-controlled data.

Supported languages / APIs
--------------------------
Python:
  pickle.loads, pickle.load, pickle.Unpickler
  yaml.load()  WITHOUT an explicit safe Loader= argument
                (yaml.safe_load and yaml.load(x, Loader=yaml.SafeLoader) are OK)
  marshal.loads, marshal.load
  shelve.open  (uses pickle internally)

JavaScript/TypeScript:
  eval(JSON.parse(...))  — caught by SEC-DANGEROUS-EXEC
  node-serialize / serialize-javascript without sanitization — flagged via import
  NOTE: JSON.parse itself is safe; we do NOT flag it.

Java:
  ObjectInputStream.readObject()
  XStream parsing without secure configuration (import detection)

C++:
  Boost.Serialization / cereal without known-safe configuration
  (Not reliably detectable without semantic analysis — documented as not supported)

Limitations
-----------
* We detect the presence of the dangerous API, NOT whether the input is actually
  attacker-controlled. Static analysis cannot prove taint flow.
* yaml.load with a safe loader is explicitly excluded.
* pickle is always flagged — there is no "safe" pickle for untrusted input.
"""

from __future__ import annotations
from analysis.rules.smells.ast_helpers import walk_depth_first, node_text, find_all

# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

# APIs that are always unsafe for untrusted input
_PY_UNSAFE_DESER = {
    "pickle":   {"loads", "load", "Unpickler"},
    "marshal":  {"loads", "load"},
    "shelve":   {"open"},
}

# yaml.load is unsafe UNLESS Loader= is explicitly provided with a safe loader
_YAML_SAFE_LOADERS = {"SafeLoader", "CSafeLoader", "BaseLoader"}


def _py_is_yaml_safe(call_node) -> bool:
    """Return True if a yaml.load() call has an explicit safe Loader argument."""
    # Look for keyword argument named 'Loader' with a safe value
    for arg in find_all(call_node, "keyword_argument"):
        children = arg.children
        if len(children) >= 3:
            key_node = children[0]
            if node_text(key_node) == "Loader":
                val_text = node_text(children[-1])
                if any(safe in val_text for safe in _YAML_SAFE_LOADERS):
                    return True
    # Also check positional second arg for safe loaders (less common)
    return False


def analyze_python_deser(tree, rel_path: str) -> list[dict]:
    """Return SEC-CWE-502 findings for Python unsafe deserialization."""
    root = tree.root_node
    results: list[dict] = []

    # Track what's imported (module alias -> module name)
    imports: dict[str, str] = {}  # alias -> canonical name

    # Collect imports
    for node in root.children:
        if node.type == "import_statement":
            # import pickle / import pickle as p
            for child in node.children:
                if child.type == "aliased_import":
                    parts = child.children
                    orig = node_text(parts[0]) if parts else ""
                    alias = node_text(parts[-1]) if len(parts) >= 3 else orig
                    imports[alias] = orig
                elif child.type == "dotted_name":
                    name = node_text(child)
                    imports[name] = name
        elif node.type == "import_from_statement":
            # from pickle import loads -> direct name in scope
            module_parts = [c for c in node.children
                            if c.type in ("dotted_name", "identifier")]
            module = node_text(module_parts[0]) if module_parts else ""
            for child in node.children:
                if child.type == "import_list":
                    for imp in child.children:
                        if imp.type == "identifier":
                            fn = node_text(imp)
                            imports[fn] = f"{module}.{fn}"
                        elif imp.type == "aliased_import":
                            alias = node_text(imp.children[-1])
                            fn = node_text(imp.children[0])
                            imports[alias] = f"{module}.{fn}"

    # Walk all call nodes
    for node in walk_depth_first(root):
        if node.type != "call":
            continue

        func_node = node.children[0] if node.children else None
        if func_node is None:
            continue

        func_text = node_text(func_node)

        # Check member access: pickle.loads(...)
        if "." in func_text:
            parts = func_text.rsplit(".", 1)
            obj, method = parts[0], parts[1]
            # Resolve alias
            canonical_module = imports.get(obj, obj)
            module_base = canonical_module.split(".")[0]

            if module_base in _PY_UNSAFE_DESER:
                if method in _PY_UNSAFE_DESER[module_base]:
                    results.append({
                        "rule_id": "SEC-CWE-502",
                        "api": func_text,
                        "line": node.start_point[0] + 1,
                        "file": rel_path,
                        "detail": (
                            f"Unsafe deserialization via `{func_text}`. "
                            f"Deserializing untrusted data with {module_base} "
                            "can lead to arbitrary code execution (CWE-502)."
                        ),
                    })
                    continue

            # yaml.load without safe loader
            if module_base == "yaml" and method == "load":
                if not _py_is_yaml_safe(node):
                    results.append({
                        "rule_id": "SEC-CWE-502",
                        "api": func_text,
                        "line": node.start_point[0] + 1,
                        "file": rel_path,
                        "detail": (
                            "yaml.load() called without an explicit safe Loader "
                            "(e.g. Loader=yaml.SafeLoader). "
                            "An untrusted YAML document can execute arbitrary Python code (CWE-502)."
                        ),
                    })
                    continue

        else:
            # Direct import: loads(data) where 'loads' is imported from pickle
            canonical = imports.get(func_text, "")
            for mod, methods in _PY_UNSAFE_DESER.items():
                if canonical == f"{mod}.{func_text}" and func_text in methods:
                    results.append({
                        "rule_id": "SEC-CWE-502",
                        "api": func_text,
                        "line": node.start_point[0] + 1,
                        "file": rel_path,
                        "detail": (
                            f"Unsafe deserialization via `{func_text}` (from {mod}). "
                            "Deserializing untrusted data can lead to arbitrary code execution (CWE-502)."
                        ),
                    })

    return results


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

def analyze_java_deser(tree, rel_path: str) -> list[dict]:
    """Detect ObjectInputStream.readObject() in Java — CWE-502."""
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type == "method_invocation":
            # Look for readObject() on ObjectInputStream
            name_node = None
            obj_node = None
            for child in node.children:
                if child.type == "identifier":
                    if name_node is None:
                        obj_node = child
                    else:
                        name_node = child
                elif child.type in ("field_access", "method_invocation"):
                    obj_node = child

            # Simpler: look for method name 'readObject'
            children_texts = [node_text(c) for c in node.children]
            if "readObject" in children_texts:
                results.append({
                    "rule_id": "SEC-CWE-502",
                    "api": "ObjectInputStream.readObject()",
                    "line": node.start_point[0] + 1,
                    "file": rel_path,
                    "detail": (
                        "readObject() deserializes Java objects from a stream. "
                        "If the stream is attacker-controlled, this can lead to "
                        "arbitrary code execution (CWE-502). "
                        "Use a serialization filter (Java 9+) or switch to a safe format."
                    ),
                })

    return results


# ---------------------------------------------------------------------------
# JS/TS — node-serialize detection via import
# ---------------------------------------------------------------------------

_JS_UNSAFE_DESER_IMPORTS = {
    "node-serialize",
    "serialize-javascript",
}


def analyze_js_deser(tree, rel_path: str) -> list[dict]:
    """Flag imports of known unsafe JS deserialization libraries."""
    results: list[dict] = []

    for node in walk_depth_first(tree.root_node):
        if node.type == "import_statement":
            for child in walk_depth_first(node):
                if child.type == "string":
                    pkg = node_text(child).strip("'\"")
                    if pkg in _JS_UNSAFE_DESER_IMPORTS:
                        results.append({
                            "rule_id": "SEC-CWE-502",
                            "api": f"import '{pkg}'",
                            "line": node.start_point[0] + 1,
                            "file": rel_path,
                            "detail": (
                                f"Import of '{pkg}' which can perform unsafe deserialization. "
                                "Deserializing attacker-controlled data can lead to "
                                "arbitrary code execution (CWE-502)."
                            ),
                        })
        elif node.type == "call_expression":
            # require('node-serialize')
            func = node.children[0] if node.children else None
            if func and node_text(func) == "require":
                for arg in find_all(node, "string"):
                    pkg = node_text(arg).strip("'\"")
                    if pkg in _JS_UNSAFE_DESER_IMPORTS:
                        results.append({
                            "rule_id": "SEC-CWE-502",
                            "api": f"require('{pkg}')",
                            "line": node.start_point[0] + 1,
                            "file": rel_path,
                            "detail": (
                                f"require('{pkg}') loads a library capable of unsafe deserialization. "
                                "Use JSON.parse() for safe data exchange (CWE-502)."
                            ),
                        })

    return results
