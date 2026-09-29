import os
from analysis.parsing.ast_parser import parse_file
from analysis.parsing.language_config import LANGUAGE_CONFIG
from analysis.finding import Finding
from analysis.rule_registry import get as get_rule

IO_NETWORK_IMPORTS = {
    'Python': ['requests', 'urllib', 'http', 'socket', 'os', 'subprocess'],
    'JavaScript': ['fs', 'http', 'https', 'axios', 'net', 'child_process'],
    'TypeScript': ['fs', 'http', 'https', 'axios', 'net', 'child_process'],
    'Java': ['java.io', 'java.nio', 'java.net', 'HttpClient'],
    'C++': ['fstream', 'sys/socket.h', 'curl/curl.h']
}

def _get_language(filename: str) -> str:
    for lang, config in LANGUAGE_CONFIG.items():
        if any(filename.endswith(ext) for ext in config["extensions"]):
            return lang
    return ''

def run_ast_security_rules(project_path: str):
    """
    Evaluates the project against AST-level security rules.
    Returns: findings (list[dict]), penalty (int).

    Internally uses Finding objects to carry rule_id, language, CWE, and
    resolution; serialises to dicts for backwards compatibility with analyze.py.
    """
    findings = []
    penalty = 0

    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']

    eval_spec = get_rule("SEC-AST-EVAL-EXEC")
    errhandling_spec = get_rule("SEC-AST-MISSING-ERRHANDLING")

    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if d not in ignored]

        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue

            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, project_path)
            tree = parse_file(filepath, lang)
            if not tree:
                continue

            config = LANGUAGE_CONFIG[lang]
            root_node = tree.root_node

            has_io = False
            has_try = False
            io_line = 1

            # Check for eval usage, try statements, and imports
            def walk(node):
                nonlocal has_io, has_try, io_line

                if node.type in config.get("try_nodes", []):
                    has_try = True

                if node.type in config.get("call_nodes", []):
                    # Check if the call is to eval/exec
                    for child in node.children:
                        if child.type == 'identifier' and child.text.decode('utf8') in ['eval', 'exec', 'system']:
                            finding = Finding(
                                rule_id="SEC-AST-EVAL-EXEC",
                                category="Security",
                                title="Dangerous Function Usage",
                                description=f"Found usage of eval()/exec()/system() in {rel_path}. Note: Flagged as High Severity injection vulnerability.",
                                severity="High",
                                rule=eval_spec.name if eval_spec else "Dangerous Function Usage",
                                language=lang,
                                cwe=eval_spec.cwe if eval_spec else None,
                                resolution=eval_spec.resolution if eval_spec else None,
                                file=rel_path,
                                line=node.start_point[0] + 1,
                            )
                            findings.append(finding.to_dict())

                # Check for IO imports
                if not has_io and node.type in config.get("import_nodes", []):
                    import_text = node.text.decode('utf8')
                    if any(io_mod in import_text for io_mod in IO_NETWORK_IMPORTS.get(lang, [])):
                        has_io = True
                        io_line = node.start_point[0] + 1

                for child in node.children:
                    walk(child)

            walk(root_node)

            if has_io and not has_try:
                finding = Finding(
                    rule_id="SEC-AST-MISSING-ERRHANDLING",
                    category="Security",
                    title="Missing Error-Handling Checks",
                    description=f"File {rel_path} imports network or I/O libraries but does not contain any try/catch blocks.",
                    severity="Medium",
                    rule=errhandling_spec.name if errhandling_spec else "Missing Error Handling",
                    language=lang,
                    cwe=errhandling_spec.cwe if errhandling_spec else None,
                    resolution=errhandling_spec.resolution if errhandling_spec else None,
                    file=rel_path,
                    line=io_line,
                )
                findings.append(finding.to_dict())

    # Approximate penalty (same logic as before)
    penalty += len([f for f in findings if f["title"] == "Dangerous Function Usage"]) * 20
    penalty += len([f for f in findings if f["title"] == "Missing Error-Handling Checks"]) * 15

    return findings, penalty
