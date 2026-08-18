import os
from analysis.parsing.ast_parser import parse_file

def _get_language(filename: str) -> str:
    if filename.endswith('.py'):
        return 'Python'
    elif filename.endswith(('.js', '.jsx')):
        return 'JavaScript'
    elif filename.endswith(('.ts', '.tsx')):
        return 'TypeScript'
    return ''

def compute_class_metrics(tree, language: str) -> list[dict]:
    classes = []
    if not tree:
        return classes
        
    root_node = tree.root_node
    
    def extract_python_class(node):
        dit = 1
        methods = 0
        
        for child in node.children:
            if child.type == 'argument_list':
                bases = [c for c in child.children if c.type == 'identifier']
                if bases:
                    dit += 1
                    
            if child.type == 'block':
                for stmt in child.children:
                    if stmt.type == 'function_definition':
                        methods += 1
                        
        lcom = max(0, methods - 1)
        
        return {
            "dit": dit,
            "public_methods": methods,
            "public_fields": 0,
            "lcom": lcom
        }

    def extract_js_class(node):
        dit = 1
        methods = 0
        fields = 0
        
        for child in node.children:
            if child.type == 'class_heritage':
                dit += 1
            if child.type == 'class_body':
                for member in child.children:
                    if member.type == 'method_definition':
                        is_private = any(c.type == 'private_property_identifier' for c in member.children)
                        if not is_private:
                            methods += 1
                    elif member.type == 'public_field_definition':
                        fields += 1
                        
        lcom = max(0, methods - 1)
        
        return {
            "dit": dit,
            "public_methods": methods,
            "public_fields": fields,
            "lcom": lcom
        }

    def walk(node):
        if language == 'Python' and node.type == 'class_definition':
            classes.append(extract_python_class(node))
        elif language in ('JavaScript', 'TypeScript') and node.type == 'class_declaration':
            classes.append(extract_js_class(node))
            
        for child in node.children:
            walk(child)

    walk(root_node)
    
    # If no classes found (e.g. functional components or scripts), treat the file as a single module with functions
    if not classes:
        methods = 0
        for child in root_node.children:
            if language == 'Python' and child.type == 'function_definition':
                methods += 1
            elif language in ('JavaScript', 'TypeScript'):
                if child.type in ('function_declaration', 'lexical_declaration', 'variable_declaration'):
                    methods += 1
        if methods > 0:
            classes.append({
                "dit": 1,
                "public_methods": methods,
                "public_fields": 0,
                "lcom": max(0, methods - 1)
            })

    return classes

def calculate_repo_averages(root_dir: str) -> dict:
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    
    all_classes = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        
        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue
                
            filepath = os.path.join(dirpath, f)
            tree = parse_file(filepath, lang)
            if tree:
                cls_metrics = compute_class_metrics(tree, lang)
                all_classes.extend(cls_metrics)
                
    if not all_classes:
        return {
            "avg_dit": 1.0,
            "avg_public_methods": 0.0,
            "avg_public_fields": 0.0,
            "avg_lcom": 0.0
        }
        
    n = len(all_classes)
    return {
        "avg_dit": sum(c["dit"] for c in all_classes) / n,
        "avg_public_methods": sum(c["public_methods"] for c in all_classes) / n,
        "avg_public_fields": sum(c["public_fields"] for c in all_classes) / n,
        "avg_lcom": sum(c["lcom"] for c in all_classes) / n
    }
