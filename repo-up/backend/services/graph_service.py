import os
import networkx as nx
from analysis.parsing.ast_parser import parse_file
from analysis.parsing.language_config import LANGUAGE_CONFIG

def _get_language(filename: str) -> str:
    for lang, config in LANGUAGE_CONFIG.items():
        if any(filename.endswith(ext) for ext in config["extensions"]):
            return lang
    return ''

def _extract_imports_from_tree(tree, language: str) -> list[str]:
    imports = []
    if not tree or language not in LANGUAGE_CONFIG:
        return imports
    
    config = LANGUAGE_CONFIG[language]
    root_node = tree.root_node
    
    def walk(node):
        if node.type in config["import_nodes"]:
            if language == 'Python':
                if node.type == 'import_from_statement':
                    for child in node.children:
                        if child.type == 'dotted_name':
                            imports.append(child.text.decode('utf8'))
                            break
                elif node.type == 'import_statement':
                    for child in node.children:
                        if child.type == 'dotted_name':
                            imports.append(child.text.decode('utf8'))
            elif language in ('JavaScript', 'TypeScript'):
                if node.type == 'import_statement':
                    for child in node.children:
                        if child.type == 'string':
                            val = child.text.decode('utf8').strip("'\"")
                            imports.append(val)
                elif node.type == 'call_expression':
                    func = None
                    args = None
                    for child in node.children:
                        if child.type == 'identifier':
                            func = child.text.decode('utf8')
                        elif child.type == 'arguments':
                            args = child
                    if func == 'require' and args:
                        for arg in args.children:
                            if arg.type == 'string':
                                val = arg.text.decode('utf8').strip("'\"")
                                imports.append(val)
            elif language == 'Java':
                for child in node.children:
                    if child.type in ('scoped_identifier', 'identifier'):
                        imports.append(child.text.decode('utf8'))
            elif language == 'C++':
                for child in node.children:
                    if child.type == 'string_literal':
                        val = child.text.decode('utf8').strip('"')
                        imports.append(val)
                        
        for child in node.children:
            walk(child)

    walk(root_node)
    return imports

def _resolve_edge(src_file: str, imp: str, lang: str, all_nodes: set) -> str:
    src_dir = os.path.dirname(src_file)
    
    if lang == 'Java':
        java_path = imp.replace('.', '/') + '.java'
        for node in all_nodes:
            if node.endswith('/' + java_path) or node == java_path:
                return node
        return None
        
    if lang == 'C++':
        resolved_base = os.path.normpath(os.path.join(src_dir, imp)).replace('\\', '/')
        if resolved_base in all_nodes:
            return resolved_base
        # Fallback for include paths relative to project root
        imp_clean = imp.replace('\\', '/')
        for node in all_nodes:
            if node.endswith('/' + imp_clean) or node == imp_clean:
                return node
        return None

    if imp.startswith('./') or imp.startswith('../'):
        resolved_base = os.path.normpath(os.path.join(src_dir, imp)).replace('\\', '/')
        for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
            test_path = resolved_base + ext
            if test_path in all_nodes:
                return test_path
    else:
        py_path = imp.replace('.', '/') if lang == 'Python' else imp
        exts = ['.py', '/__init__.py', '', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']
        for ext in exts:
            test_path = py_path + ext
            if test_path in all_nodes:
                return test_path
            if src_dir:
                test_rel = os.path.normpath(os.path.join(src_dir, test_path)).replace('\\', '/')
                if test_rel in all_nodes:
                    return test_rel
        
        if lang in ('JavaScript', 'TypeScript'):
            for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                suffix = py_path + ext
                if not suffix.startswith('/'):
                    suffix = '/' + suffix
                for node in all_nodes:
                    if node.endswith(suffix):
                        return node
    return None

def build_dependency_graph(root_dir: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    file_imports = {}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        
        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue
                
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, root_dir).replace('\\', '/')
            graph.add_node(rel_path)
            
            tree = parse_file(filepath, lang)
            if tree:
                imports = _extract_imports_from_tree(tree, lang)
                file_imports[rel_path] = imports
                
    all_nodes = set(graph.nodes())
    
    for src_file, imports in file_imports.items():
        lang = _get_language(src_file)
        for imp in imports:
            target = _resolve_edge(src_file, imp, lang, all_nodes)
            if target:
                graph.add_edge(src_file, target)

    return graph

def build_dependency_graph_stream(root_dir: str):
    ignored = ['node_modules', 'venv', '.venv', '.git', '__pycache__']
    file_imports = {}
    all_nodes = set()
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        for f in filenames:
            lang = _get_language(f)
            if not lang:
                continue
                
            filepath = os.path.join(dirpath, f)
            rel_path = os.path.relpath(filepath, root_dir).replace('\\', '/')
            all_nodes.add(rel_path)
            yield ("node", rel_path)
            
            tree = parse_file(filepath, lang)
            if tree:
                imports = _extract_imports_from_tree(tree, lang)
                file_imports[rel_path] = imports
                
    for src_file, imports in file_imports.items():
        lang = _get_language(src_file)
        for imp in imports:
            target = _resolve_edge(src_file, imp, lang, all_nodes)
            if target:
                yield ("edge", src_file, target)

def serialize_graph(graph: nx.DiGraph) -> dict:
    """Serializes a networkx DiGraph into a JSON-friendly dict."""
    return {
        "nodes": [{"id": n, "label": os.path.basename(n)} for n in graph.nodes()],
        "edges": [{"source": u, "target": v} for u, v in graph.edges()]
    }
