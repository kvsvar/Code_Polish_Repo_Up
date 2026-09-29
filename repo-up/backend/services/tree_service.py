import os

def generate_project_tree(dir_path: str, depth: int = 0) -> list[str]:
    tree = []
    try:
        items = sorted(os.listdir(dir_path))
    except Exception:
        return tree

    for item in items:
        # Skip common large directories and system files
        if item in ['.git', 'node_modules', 'venv', '.venv', '__pycache__'] or item.startswith('.DS_Store'):
            continue
            
        full_path = os.path.join(dir_path, item)
        indent = "  " * depth
        if os.path.isdir(full_path):
            tree.append(f"{indent}{item}/")
            tree.extend(generate_project_tree(full_path, depth + 1))
        else:
            tree.append(f"{indent}{item}")
            
    return tree
