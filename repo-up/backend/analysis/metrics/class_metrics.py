import os
from analysis.parsing.ast_parser import parse_file
from analysis.parsing.language_config import LANGUAGE_CONFIG

def _get_language(filename: str) -> str:
    for lang, config in LANGUAGE_CONFIG.items():
        if any(filename.endswith(ext) for ext in config["extensions"]):
            return lang
    return ''

def compute_class_metrics(tree, language: str, filepath: str = "") -> list[dict]:
    classes = []
    if not tree or language not in LANGUAGE_CONFIG:
        return classes
        
    config = LANGUAGE_CONFIG[language]
    root_node = tree.root_node
    
    def extract_class(node):
        class_name = "Unknown"
        for child in node.children:
            if child.type in ('identifier', 'type_identifier', 'name'):
                class_name = child.text.decode('utf8')
                break

        dit = 1
        methods = 0
        fields = 0
        
        def walk_class_body(n):
            nonlocal dit, methods, fields
            for child in n.children:
                if child.type in config.get("inheritance_nodes", []):
                    dit += 1
                elif child.type in config["method_nodes"]:
                    is_private = False
                    if language in ('JavaScript', 'TypeScript'):
                        is_private = any(c.type == 'private_property_identifier' for c in child.children)
                    if not is_private:
                        methods += 1
                elif child.type == 'public_field_definition':
                    fields += 1
                
                # Stop walking if we hit another class to avoid counting its methods
                if child.type not in config["class_nodes"]:
                    walk_class_body(child)

        walk_class_body(node)
        
        lcom = max(0, methods - 1)
        
        return {
            "name": class_name,
            "filepath": filepath,
            "dit": dit,
            "public_methods": methods,
            "public_fields": fields,
            "lcom": lcom,
            "line": node.start_point[0] + 1
        }

    def walk(node):
        if node.type in config["class_nodes"]:
            classes.append(extract_class(node))
            
        for child in node.children:
            walk(child)

    walk(root_node)
    
    # If no classes found (e.g. functional components or scripts), treat the file as a single module with functions
    if not classes:
        methods = 0
        def count_funcs(n):
            nonlocal methods
            for child in n.children:
                if child.type in config["method_nodes"]:
                    methods += 1
                if child.type not in config["class_nodes"]:
                    count_funcs(child)
        count_funcs(root_node)
        
        if methods > 0:
            classes.append({
                "name": "Module Level",
                "filepath": filepath,
                "dit": 1,
                "public_methods": methods,
                "public_fields": 0,
                "lcom": max(0, methods - 1),
                "line": 1
            })

    return classes

def calculate_repo_averages(root_dir: str):
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    
    all_classes = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        
        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue
                
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, root_dir)
            tree = parse_file(filepath, lang)
            if tree:
                cls_metrics = compute_class_metrics(tree, lang, rel_path)
                all_classes.extend(cls_metrics)
                
    findings = []
    for c in all_classes:
        if c["public_methods"] > 15:
            findings.append({
                "category": "Metrics",
                "title": "High WMC (God Class)",
                "description": f"Class '{c['name']}' has {c['public_methods']} public methods. Very high WMC suggests the class is doing too much and lacks cohesion.",
                "severity": "High",
                "file": c["filepath"],
                "line": c.get("line")
            })
        if c["dit"] >= 3:
            findings.append({
                "category": "Metrics",
                "title": "Deep Inheritance Tree (DIT)",
                "description": f"Class '{c['name']}' has a DIT of {c['dit']}. Deep inheritance chains make the system harder to trace and maintain.",
                "severity": "Medium",
                "file": c["filepath"],
                "line": c.get("line")
            })
        if c["lcom"] > 10:
            findings.append({
                "category": "Metrics",
                "title": "Low Cohesion (LCOM)",
                "description": f"Class '{c['name']}' has an LCOM of {c['lcom']}, indicating that its methods do not relate to the same data fields.",
                "severity": "Medium",
                "file": c["filepath"],
                "line": c.get("line")
            })
                
    if not all_classes:
        return {
            "avg_dit": 1.0,
            "avg_public_methods": 0.0,
            "avg_public_fields": 0.0,
            "avg_lcom": 0.0
        }, findings
        
    n = len(all_classes)
    averages = {
        "avg_dit": sum(c["dit"] for c in all_classes) / n,
        "avg_public_methods": sum(c["public_methods"] for c in all_classes) / n,
        "avg_public_fields": sum(c["public_fields"] for c in all_classes) / n,
        "avg_lcom": sum(c["lcom"] for c in all_classes) / n
    }
    return averages, findings
