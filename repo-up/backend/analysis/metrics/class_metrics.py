"""
class_metrics.py — CK-style class/module metric extraction via Tree-sitter ASTs.

Metrics computed (proxies — exact definitions per thresholds.py)
----------------------------------------------------------------
DIT  — Depth of Inheritance Tree.
       Python bug-fix: ``argument_list`` children that contain dotted-name
       (base classes) are counted, but plain ``argument_list`` with no
       dotted-name children (e.g. metaclasses) no longer inflate DIT.

WMC proxy  — public method count per class/module.
       "Public" for JS/TS = excludes names starting with ``#`` (private fields).
       For Python, every function_definition is treated as public (Python has
       no enforced access modifier; underscore convention is NOT applied here).

LCOM proxy — methods − 1 per class (crude cohesion indicator, not full LCOM4).
       A value of 0 means one method (perfectly cohesive by this proxy).

Public fields — count of ``public_field_definition`` AST nodes (JS/TS classes).
                Always 0 for Python/Java/C++ in the current parser.
"""

import os
import logging
from analysis.parsing.ast_parser import parse_file
from analysis.parsing.language_config import LANGUAGE_CONFIG
from analysis.finding import Finding
from analysis.rule_registry import get as get_rule

log = logging.getLogger(__name__)


def _get_language(filename: str) -> str:
    for lang, config in LANGUAGE_CONFIG.items():
        if any(filename.endswith(ext) for ext in config["extensions"]):
            return lang
    return ""


def compute_class_metrics(tree, language: str, filepath: str = "") -> list[dict]:
    """Return a list of per-class metric dicts for *tree*.

    Returns an empty list when the file has no classes and no functions.
    """
    classes: list[dict] = []
    if not tree or language not in LANGUAGE_CONFIG:
        return classes

    config = LANGUAGE_CONFIG[language]
    root_node = tree.root_node

    def extract_class(node) -> dict:
        class_name = "Unknown"
        for child in node.children:
            if child.type in ("identifier", "type_identifier", "name"):
                class_name = child.text.decode("utf8")
                break

        # DIT starts at 1 (the class itself)
        dit = 1
        methods = 0
        fields = 0

        def walk_class_body(n) -> None:
            nonlocal dit, methods, fields
            for child in n.children:
                # --- Inheritance depth ---
                if child.type in config.get("inheritance_nodes", []):
                    if language == "Python":
                        # argument_list is used for bases AND for metaclass=…
                        # Only count if it contains dotted_name children (actual bases).
                        has_base = any(
                            c.type in ("identifier", "dotted_name")
                            for c in child.children
                        )
                        if has_base:
                            dit += 1
                    else:
                        dit += 1

                # --- Method count (WMC proxy) ---
                elif child.type in config["method_nodes"]:
                    is_private = False
                    if language in ("JavaScript", "TypeScript"):
                        # JS/TS private fields use ``#name`` syntax
                        is_private = any(
                            c.type == "private_property_identifier"
                            for c in child.children
                        )
                    if not is_private:
                        methods += 1

                # --- Public fields (JS/TS) ---
                elif child.type == "public_field_definition":
                    fields += 1

                # Don't recurse into nested classes
                if child.type not in config["class_nodes"]:
                    walk_class_body(child)

        walk_class_body(node)

        # LCOM proxy: methods − 1 (floored at 0)
        lcom = max(0, methods - 1)

        return {
            "name": class_name,
            "filepath": filepath,
            "dit": dit,
            "public_methods": methods,   # WMC proxy
            "public_fields": fields,
            "lcom": lcom,                # LCOM proxy
            "line": node.start_point[0] + 1,
        }

    def walk(node) -> None:
        if node.type in config["class_nodes"]:
            classes.append(extract_class(node))
        for child in node.children:
            walk(child)

    walk(root_node)

    # If no classes found (functional / script files), treat the whole file as
    # one module-level unit, counting top-level function definitions only.
    if not classes:
        methods = 0

        def count_funcs(n) -> None:
            nonlocal methods
            for child in n.children:
                if child.type in config["method_nodes"]:
                    methods += 1
                if child.type not in config["class_nodes"]:
                    count_funcs(child)

        count_funcs(root_node)

        if methods > 0:
            classes.append(
                {
                    "name": "Module Level",
                    "filepath": filepath,
                    "dit": 1,
                    "public_methods": methods,  # WMC proxy
                    "public_fields": 0,
                    "lcom": max(0, methods - 1),  # LCOM proxy
                    "line": 1,
                }
            )

    return classes


def calculate_repo_averages(root_dir: str) -> tuple[dict, list[dict]]:
    """Walk *root_dir* and return averaged class metrics + per-class findings.

    Returns
    -------
    (averages_dict, findings_list)
    averages_dict has keys: avg_dit, avg_public_methods, avg_public_fields, avg_lcom.
    Falls back to safe defaults (no crash) when the repo has no parseable files.
    """
    ignored = {"node_modules", "venv", ".venv", ".git", "__pycache__"}
    all_classes: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]

        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue

            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, root_dir)
            try:
                tree = parse_file(filepath, lang)
            except Exception:
                log.exception("Failed to parse %s", filepath)
                continue

            if tree:
                try:
                    cls_metrics = compute_class_metrics(tree, lang, rel_path)
                    all_classes.extend(cls_metrics)
                except Exception:
                    log.exception("Failed to compute class metrics for %s", filepath)

    findings: list[dict] = []
    _wmc_spec  = get_rule("METRIC-HIGH-WMC")
    _dit_spec  = get_rule("METRIC-DEEP-DIT")
    _lcom_spec = get_rule("METRIC-LOW-COHESION")
    for c in all_classes:
        if c["public_methods"] > 15:
            findings.append(
                Finding(
                    rule_id="METRIC-HIGH-WMC",
                    category="Metrics",
                    title="High WMC -- many public methods",
                    description=(
                        f"'{c['name']}' has {c['public_methods']} public methods "
                        f"(WMC proxy). A high count suggests the class has too many "
                        f"responsibilities and may benefit from decomposition."
                    ),
                    severity="High",
                    rule=_wmc_spec.name if _wmc_spec else "High WMC",
                    resolution=_wmc_spec.resolution if _wmc_spec else None,
                    file=c["filepath"],
                    line=c.get("line"),
                ).to_dict()
            )
        if c["dit"] >= 3:
            findings.append(
                Finding(
                    rule_id="METRIC-DEEP-DIT",
                    category="Metrics",
                    title="Deep Inheritance (DIT >= 3)",
                    description=(
                        f"'{c['name']}' has an inheritance depth of {c['dit']}. "
                        f"Deep chains can make behaviour harder to trace and test."
                    ),
                    severity="Medium",
                    rule=_dit_spec.name if _dit_spec else "Deep DIT",
                    resolution=_dit_spec.resolution if _dit_spec else None,
                    file=c["filepath"],
                    line=c.get("line"),
                ).to_dict()
            )
        if c["lcom"] > 10:
            findings.append(
                Finding(
                    rule_id="METRIC-LOW-COHESION",
                    category="Metrics",
                    title="Low Cohesion (LCOM proxy > 10)",
                    description=(
                        f"'{c['name']}' has a LCOM proxy value of {c['lcom']} "
                        f"(methods - 1). A high value suggests the class may be "
                        f"doing too many unrelated things."
                    ),
                    severity="Medium",
                    rule=_lcom_spec.name if _lcom_spec else "Low Cohesion",
                    resolution=_lcom_spec.resolution if _lcom_spec else None,
                    file=c["filepath"],
                    line=c.get("line"),
                ).to_dict()
            )

    if not all_classes:
        return (
            {
                "avg_dit": 1.0,
                "avg_public_methods": 0.0,
                "avg_public_fields": 0.0,
                "avg_lcom": 0.0,
            },
            findings,
        )

    n = len(all_classes)
    averages = {
        "avg_dit":            sum(c["dit"]            for c in all_classes) / n,
        "avg_public_methods": sum(c["public_methods"] for c in all_classes) / n,
        "avg_public_fields":  sum(c["public_fields"]  for c in all_classes) / n,
        "avg_lcom":           sum(c["lcom"]           for c in all_classes) / n,
    }
    return averages, findings
